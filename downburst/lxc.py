import paramiko
import re
import sys
import random
import tempfile
import logging

from . import discover
from . import template
from . import meta

log = logging.getLogger(__name__)

imagedir = "/var/lib/libvirt/images"
lxcdir = "/var/lib/lxc"

def createlxc(args, meta_data, user_data, distro, distroversion, arch):
    hostname = args.lxc
    guestname = args.name
    networks = meta_data.get('downburst', {}).get('networks')
    guestdir = imagedir + '/lxc/' + guestname + '/'

    #connect to SSH
    client = ssh(hostname)

    #See if lxc command is on the remote server:
    try:
        runcommand(client, 'sudo lxc-ls')
    except Exception as e:
        raise  type(e)(e.message + '\n\nError: LXC not installed on host. Try running sudo apt-get install lxc; sudo service lxc start')

    #Using ls due to not being able to use wildcard to search for files
    out = runcommand(client, 'sudo ls -1 ' + imagedir)
    list = re.findall('.*-cloudimg-.*', out)
    imageprefix = distro + '-' + distroversion + '-(\d+)'
    imagesuffix = '-cloudimg-' + arch + '.tar.gz'
    imagestring = imageprefix + imagesuffix

    #Look for .tar.gz in correct name format in libvirt folder.
    file = discover.search(imagestring, list)
    if not file:
        #Acceptable image file not on server. Download:
        log.debug('Discovering cloud images...')
        image = discover.get(distro=distro, distroversion=distroversion, arch=arch, lxc=True)
        log.debug('Will fetch serial number: %s', image['serial'])
        url= image['url']
        filename = url.split('/')[-1]
        print "Downloading image from " + url
        print "Do not hit control-c"
        out = runcommand(client, 'sudo wget -q -O ' + imagedir + '/' + filename + ' ' + url)
        file = imagedir + '/' + filename
    else:
        #Found image file
        print "Found lxc template file on host: " + file
        file = imagedir + '/' + file

    #Since we are running in a non-standard location make the directory incase it doesn't exist
    runcommand(client, 'sudo mkdir -p ' + imagedir + '/lxc/')
    try:
        runcommand(client, 'sudo mkdir ' + guestdir)
    except Exception:
        raise Exception('Root FS Directory: ' + guestdir + ' Already exists on the remote host. Stopping')

    #Get mac and network from cloud metadata/yaml or generate/use default if none exists.
    if networks is None:
        networks = [{}]
    for net in networks:
        mac = net.get('mac')
        source = net.get('source')
    if not mac:
        mac = randommac()
    if not source:
        source = 'front'
    systemd=False

    if distro == 'rhel' or distro == 'centos':
        if float(distroversion) >= 7.0:
            systemd=True
    if distro == 'fedora':
        if int(distroversion) >= 17:
            systemd=True
    if systemd:
        log.info('This guest uses sytemd. New-ish lxc needed. Probably > 1.0 is ok. (trusty host)')
    configdata = '\n'.join(template.lxc(guestname=guestname, network=source, mac=mac, rootfs=guestdir, systemd=systemd))
    meta_raw = meta.read_meta(meta_data)
    user_raw = '#cloud-config-archive\n' + meta.read_meta(user_data)

    #temporary config file as running lxc-create will import it to the right spot.
    configfile = tempfile.NamedTemporaryFile().name

    #Push LXC config file
    putfile(client, configfile, configdata)
    try:
        runcommand(client, 'sudo lxc-create -n ' + guestname + ' -f ' + configfile)
    except Exception:
        raise Exception('Failed to create guest. Does it already exist?')

    runcommand(client, 'sudo rm ' + configfile)

    #Push cloud-init data.
    cloudpath = guestdir + '/var/lib/cloud/seed/nocloud-net'
    runcommand(client, 'sudo tar xpf ' + file + ' -C ' + guestdir)
    runcommand(client, 'sudo mkdir -p ' + cloudpath)
    putfile(client, cloudpath + '/meta-data', meta_raw)
    putfile(client, cloudpath + '/user-data', user_raw)

    #Start guest after creating it.
    runcommand(client, 'sudo lxc-start -n ' + guestname + ' -d')
    client.close()
    print "Guest Created"
    return

def destroylxc(args):
    hostname = args.lxc
    guestname = args.name

    #Setup SSH connection
    client = ssh(hostname)
    try:
        out = runcommand(client, 'sudo lxc-destroy -n ' + guestname + ' -f')
    except Exception as e:
        raise  type(e)(e.message + "\n\nError: Destroying the guest failed. It needs to be manually removed")
    print "Guest Destroyed. Older versions of lxc need the container"
    print "directory manually cleared out. To do this run:"
    print "ssh ubuntu@" + hostname + " rm -Rvf " + lxcdir + "/" + guestname

def runcommand(client, command):
    stdin, stdout, stderr = client.exec_command(command)

    #Raise exception if non clean exit status and print stdout/err. Otherwise return stdout.
    if stdout.channel.recv_exit_status() != 0:
        raise Exception('Command: \'' + command + '\' did not run succesfully on remote machine (exit status non zero)\nStdout: ' + stdout.read() + 'Stderr: ' + stderr.read())
    return stdout.read()

def putfile(client, file, contents):
    #Write to temporarily file then move with sudo (to get around users lack of root privileges)
    tmpf = tempfile.NamedTemporaryFile().name
    sftp = client.open_sftp()
    f = sftp.open(tmpf, 'wb')
    f.write(contents)
    f.close()
    runcommand(client, 'sudo mv -v ' + tmpf + ' ' + file)

def ssh(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(hostname, username='ubuntu')
    return client

def randommac():
    ETH_ALEN = 3
    addr = [random.randint(0, 255) for x in range(ETH_ALEN)]
    # clear multicast bit
    addr[0] &= 0xfe

    # set local assignment bit (IEEE802)
    addr[0] |= 0x02

    randommac = '52:54:00:' + ':'.join(['%02x' % x for x in addr])
    return randommac
