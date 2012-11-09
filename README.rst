==========================================================
 Downburst -- fast Ubuntu Cloud image creation on libvirt
==========================================================

Downburst is a tool for quickly creating virtual machines on
libvirt. It uses Ubuntu's Cloud Images and qcow2 copy-on-write clones
to make a VM creation practically instantaneous, customizing them at
boot time with cloud-init.

For more information on Ubuntu Cloud Images, please refer to:

- https://cloud.ubuntu.com/
- https://help.ubuntu.com/community/UEC/Images
- https://help.ubuntu.com/community/CloudInit
- https://cloud-images.ubuntu.com/


Installation
============

You can install Downburst like any other Python package, but it also
comes with a convenient bootstrap script that sets it up in a virtual
environment under the source directory. Just run::

	git clone https://github.com/ceph/downburst.git
	cd downburst
	./bootstrap

And from there on, use::

	./virtualenv/bin/downburst ARGS..

You can also symlink that to e.g. ``~/bin/``.


Usage
=====

You need to give a unique name to your vm. This will become the
hostname of the vm, and the libvirt domain name. Run::

	downburst -C URI create NAME

The URI is the alias set in uri_aliases in ~/.libvirt/libvirt.conf. Example::

    uri_aliases = [
        'vercoi01=qemu+ssh://ubuntu@vercoi01.front.sepia.ceph.com/system?no_tty',
        'vercoi02=qemu+ssh://ubuntu@vercoi02.front.sepia.ceph.com/system?no_tty',
        'vercoi03=qemu+ssh://ubuntu@vercoi03.front.sepia.ceph.com/system?no_tty',
        'vercoi04=qemu+ssh://ubuntu@vercoi04.front.sepia.ceph.com/system?no_tty',
        'vercoi05=qemu+ssh://ubuntu@vercoi05.front.sepia.ceph.com/system?no_tty',
        'vercoi06=qemu+ssh://ubuntu@vercoi06.front.sepia.ceph.com/system?no_tty',
        'vercoi07=qemu+ssh://ubuntu@vercoi07.front.sepia.ceph.com/system?no_tty',
        'vercoi08=qemu+ssh://ubuntu@vercoi08.front.sepia.ceph.com/system?no_tty',
        'senta01=qemu+ssh://ubuntu@senta01.front.sepia.ceph.com/system?no_tty',
        'senta02=qemu+ssh://ubuntu@senta02.front.sepia.ceph.com/system?no_tty',
        'senta03=qemu+ssh://ubuntu@senta03.front.sepia.ceph.com/system?no_tty',
        'senta04=qemu+ssh://ubuntu@senta04.front.sepia.ceph.com/system?no_tty',
        ]


You can delete a guest with (use caution)::

        downburst -c URI destroy NAME

By default, your local SSH public key (grabbed from
``~/.ssh/id_rsa.pub``) is authorized to log in as ``ubuntu``.

You can also pass in EC2-style ``meta-data`` and ``user-data``
snippets; if you repeat the argument, the files will be merged::

	downburst create --meta-data=FILE.meta.yaml \
	  --user-data=FILE.user.yaml NAME

See ``doc/examples/`` for ideas on meta-data and user-data usage, and
explore the Ubuntu links above.

Valid Downburst options in meta yaml with their defaults if undefined:

disk:          (disk space)
                Default 10G. Example: 20G
ram:           (ram amount)
                Default 512M. Example: 2G
cpu:           (cpu/core count)
                Default 1. Example 4
networks:      (what nics/networks/mac addresses)::

                Default Nat. Example:
                    - source: front
                      mac: 52:54:00:5a:aa:ee

distro:        (distro type)
                Default ubuntu. Example centos
distroversion: (distro version)
                Default (if ubuntu) "12.04". Example "12.10"

Distro and distroversion can also be set during command line creation with --distro=value and --distroversion=value

Static SSH key generation
=========================

Downburst also includes a utility to create static SSH keys, for when
you want to delete and recreate the vm repeatedly, but not have SSH
complain all the time.

To set it up, run this once::

	downburst gen-ssh-key >NAME.user.yaml

And from there on, recreate the vm (after deleting it) with::

	downburst create --user-data=NAME.user.yaml NAME
