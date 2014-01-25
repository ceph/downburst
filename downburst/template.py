from lxml import etree
import pkg_resources

def parse_rbd_monitor(monitorlist):
    monitors = dict()
    for monitor in monitorlist.split(','):
        port = '6789'
        if ':' in monitor:
            port = monitor.split(':')[1]
            monitor = monitor.split(':')[0]
        monitors[monitor] = port
    return monitors

def rbd_pool(
    name,
    pool,
    monitorlist,
    user,
    secret
    ):

    root = etree.Element('pool', type='rbd')
    etree.SubElement(root, 'name').text = name
    rsource = etree.SubElement(root, 'source')
    etree.SubElement(rsource,'name').text = pool

    for monitor, port in parse_rbd_monitor(monitorlist).iteritems():
        etree.SubElement(rsource, 'host', name=monitor, port=port)

    if user:
         auth = etree.SubElement(rsource, 'auth', username=user, type='ceph')
         etree.SubElement(auth, 'secret', uuid=secret)
    return root

def rbd_volume(
    name,
    capacity,
    pool,
    ):
    root = etree.Element('volume')
    etree.SubElement(root, 'name').text = name
    etree.SubElement(root, 'source')
    etree.SubElement(root, 'capacity', unit='bytes').text = str(capacity)
    etree.SubElement(root, 'allocation', unit='bytes').text =  str(capacity)
    target = etree.SubElement(root, 'target')
    etree.SubElement(target, 'path').text = 'rbd:{pool}/{name}'.format(pool=pool, name=name)
    etree.SubElement(target, 'format', type='unknown')
    permissions = etree.SubElement(target, 'permissions')
    etree.SubElement(permissions, 'mode').text = '00'
    etree.SubElement(permissions, 'owner').text = '0'
    etree.SubElement(permissions, 'group').text = '0'
    return root

def volume(
    name,
    capacity=0,
    format_=None,
    sparse=True,
    raw = False,
    ):
    root = etree.Element('volume')
    etree.SubElement(root, 'name').text = name
    etree.SubElement(root, 'capacity').text = '{0:d}'.format(capacity)
    if sparse:
        etree.SubElement(root, 'allocation').text = '0'
    if raw:
        _format = 'raw'
    target = etree.SubElement(root, 'target')
    if format_ is None:
        format_ = 'qcow2'
    etree.SubElement(target, 'format', type=format_)
    return root


def volume_clone(
    name,
    parent_vol,
    capacity=None,
    raw = False
    ):
    (_type_, parent_capacity, _allocation) = parent_vol.info()
    if capacity is None:
        capacity = parent_capacity
    type = 'qcow2'
    sparse = False
    if raw:
       type = 'raw'
       sparse = False
    root = volume(name=name, capacity=capacity, sparse=sparse, raw=raw)
    backing = etree.SubElement(root, 'backingStore')
    etree.SubElement(backing, 'format', type=type)
    etree.SubElement(backing, 'path').text = parent_vol.key()
    return root


def domain(
    name,
    disk_key,
    iso_key,
    ram=None,
    cpus=None,
    networks=None,
    additional_disks_key=None,
    rbd_disks_key=None,
    rbd_details=None,
    hypervisor='kvm',
    raw = False
    ):
    with pkg_resources.resource_stream('downburst', 'template.xml') as f:
        tree = etree.parse(f)
    (domain,) = tree.xpath('/domain')
    domain.set('type', hypervisor)

    n = etree.SubElement(domain, 'name')
    n.text = name

    # <disk type='file' device='disk'>
    #   <driver name='qemu' type='qcow2'/>
    #   <source file='/var/lib/libvirt/images/NAME.img'/>
    #   <target dev='vda' bus='virtio'/>
    # </disk>
    type = 'qcow2'
    if raw:
        type = 'raw'
    (devices,) = tree.xpath('/domain/devices')
    disk = etree.SubElement(devices, 'disk', type='file', device='disk')
    etree.SubElement(disk, 'driver', name='qemu', type=type)
    etree.SubElement(disk, 'source', file=disk_key)
    etree.SubElement(disk, 'target', dev='vda', bus='virtio')
    letters = 'abcdefghijklmnopqrstuvwxyz'
    x = 0
    if additional_disks_key is not None:
        for key in additional_disks_key:
            x += 1

            # Skip a because vda = boot drive. Drives should start
            # at vdb and continue: vdc, vdd, etc...

            blockdevice = 'vd' + letters[x]

            # <disk type='file' device='disk'>
            #   <driver name='qemu' type='raw'/>
            #   <source file='/var/lib/libvirt/images/NAME.img'/>
            #   <target dev='vdX' bus='virtio'/>
            # </disk>
            (devices,) = tree.xpath('/domain/devices')
            disk = etree.SubElement(devices, 'disk', type='file', device='disk')
            etree.SubElement(disk, 'driver', name='qemu', type='raw')
            etree.SubElement(disk, 'source', file=key)
            etree.SubElement(disk, 'target', dev=blockdevice, bus='virtio')
    if rbd_disks_key is not None:
        for key in rbd_disks_key:
            x += 1

            # Skip a because vda = boot drive. Drives should start
            # at vdb and continue: vdc, vdd, etc...

            blockdevice = 'vd' + letters[x]

            # <disk type='file' device='disk'>
            #   <driver name='qemu' type='raw'/>
            #   <source file='/var/lib/libvirt/images/NAME.img'/>
            #   <target dev='vdX' bus='virtio'/>
            # </disk>

            (devices,) = tree.xpath('/domain/devices')
            disk = etree.SubElement(devices, 'disk', type='network')
            etree.SubElement(disk, 'driver', name='qemu', type='raw')
            rsource = etree.SubElement(disk, 'source', protocol='rbd', name=key)
            for monitor, port in parse_rbd_monitor(rbd_details['ceph_cluster_monitors']).iteritems():
                etree.SubElement(rsource, 'host', name=monitor, port=port)

            etree.SubElement(disk, 'target', dev=blockdevice, bus='virtio')
            if rbd_details['ceph_cluster_user']:
                auth = etree.SubElement(disk, 'auth', username=rbd_details['ceph_cluster_user'])
                etree.SubElement(auth, 'secret', type='ceph', usage=rbd_details['ceph_cluster_secret'])

    # <disk type='file' device='cdrom'>
    #   <driver name='qemu' type='raw'/>
    #   <source file='/var/lib/libvirt/images/cloud-init.chef03.iso'/>
    #   <target dev='hdc' bus='ide'/>
    #   <readonly/>
    # </disk>
    disk = etree.SubElement(devices, 'disk', type='file', device='cdrom')
    etree.SubElement(disk, 'driver', name='qemu', type='raw')
    etree.SubElement(disk, 'source', file=iso_key)
    etree.SubElement(disk, 'target', dev='hdc', bus='ide')

    if ram is not None:
        # default unit is kibibytes, and libvirt <0.9.11 doesn't
        # support changing that
        ram = int(round(ram/1024.0))
        (memory,) = tree.xpath('/domain/memory')
        memory.text = '{ram:d}'.format(ram=ram)

    if cpus is not None:
        (vcpu,) = tree.xpath('/domain/vcpu')
        vcpu.text = '{cpus:d}'.format(cpus=cpus)

    # <interface type='network'>
    #   <source network='default'/>
    #   <model type='virtio'/>
    # </interface>
    if networks is None:
        networks = [{}]
    for net in networks:
        net_elem = etree.SubElement(
            devices,
            'interface',
            type='network',
            )
        etree.SubElement(net_elem, 'model', type='virtio')
        etree.SubElement(
            net_elem,
            'source',
            network=net.get('source', 'default'),
            )
        mac = net.get('mac')
        if mac is not None:
            # <mac address='52:54:00:01:02:03'/>
            etree.SubElement(net_elem, 'mac', address=mac)

    return tree
