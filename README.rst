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

You can install Downburst like any other Python package, but it comes
with a convenient bootstrap script that sets it up in a virtual
environment under the source directory. Just run::

	./bootstrap

And from there on, use

	./virtualenv/bin/downburst ARGS..

You can also symlink that to e.g. ``~/bin/``.


Usage
=====

You need to give a unique name to your vm. This will become the
hostname of the vm, and the libvirt domain name. Run::

	downburst create NAME

By default, your local SSH public key (grabbed from
``~/.ssh/id_rsa.pub``) is authorized to log in as ``ubuntu``.

You can also pass in EC2-style ``meta-data`` and ``user-data``
snippets; if you repeat the argument, the files will be merged::

	downburst create --meta-data=FILE.meta.yaml \
	  --user-data=FILE.user.yaml NAME

See ``doc/examples/`` for ideas on meta-data and user-data usage, and
explore the Ubuntu links above.


Static SSH key generation
=========================

Downburst also includes a utility to create static SSH keys, for when
you want to delete and recreate the vm repeatedly, but not have SSH
complain all the time.

To set it up, run this once::

	downburst generate-ssh-key >NAME.user.yaml

And from there on, recreate the vm (after deleting it) with::

	downburst create --user-data=NAME.user.yaml NAME
