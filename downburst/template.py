from lxml import etree
import pkg_resources


def fill(
    name,
    disk_key,
    iso_key,
    ):
    with pkg_resources.resource_stream('downburst', 'template.xml') as f:
        tree = etree.parse(f)
    (domain,) = tree.xpath('/domain')

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

    return tree
