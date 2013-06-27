from lxml import etree
import pkg_resources


def lxc(
    network,
    mac,
    rootfs,
    ):
    config =[
        'lxc.tty=5',
        'lxc.pts=1024',
        'lxc.network.type = veth',
        'lxc.network.flags = up',
        'lxc.network.link = br-{network}'.format(network=network),
        'lxc.network.hwaddr = {mac}'.format(mac=mac),
        'lxc.rootfs = {rootfs}'.format(rootfs=rootfs),
        ],
    return config

def volume(
    name,
    capacity=0,
    format_=None,
    sparse=True,
    ):
    root = etree.Element('volume')
    etree.SubElement(root, 'name').text = name
    etree.SubElement(root, 'capacity').text = '{0:d}'.format(capacity)
    if sparse:
        etree.SubElement(root, 'allocation').text = '0'
    target = etree.SubElement(root, 'target')
    if format_ is None:
        format_ = 'qcow2'
    etree.SubElement(target, 'format', type=format_)
    return root


def volume_clone(
    name,
    parent_vol,
    capacity=None,
    ):
    (_type_, parent_capacity, _allocation) = parent_vol.info()
    if capacity is None:
        capacity = parent_capacity
    root = volume(name=name, capacity=capacity)

    backing = etree.SubElement(root, 'backingStore')
    etree.SubElement(backing, 'format', type='qcow2')
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
    hypervisor='kvm'
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
    (devices,) = tree.xpath('/domain/devices')
    disk = etree.SubElement(devices, 'disk', type='file', device='disk')
    etree.SubElement(disk, 'driver', name='qemu', type='qcow2')
    etree.SubElement(disk, 'source', file=disk_key)
    etree.SubElement(disk, 'target', dev='vda', bus='virtio')

    if additional_disks_key is not None:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        x = 0
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
