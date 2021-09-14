import pytest

from .. import util

capabilities_xml_text ="""<capabilities>

  <host>
    <uuid>f39760cc-2adc-11b2-a85c-c6cfbb1a38ee</uuid>
    <cpu>
      <arch>x86_64</arch>
      <model>Skylake-Client-IBRS</model>
      <vendor>Intel</vendor>
      <microcode version='234'/>
      <counter name='tsc' frequency='2591998000' scaling='no'/>
      <topology sockets='1' dies='1' cores='6' threads='2'/>
      <feature name='ds'/>
      <feature name='acpi'/>
      <feature name='ss'/>
      <feature name='ht'/>
      <feature name='tm'/>
      <feature name='pbe'/>
      <feature name='dtes64'/>
      <feature name='monitor'/>
      <feature name='ds_cpl'/>
      <feature name='vmx'/>
      <feature name='smx'/>
      <feature name='est'/>
      <feature name='tm2'/>
      <feature name='xtpr'/>
      <feature name='pdcm'/>
      <feature name='osxsave'/>
      <feature name='tsc_adjust'/>
      <feature name='clflushopt'/>
      <feature name='intel-pt'/>
      <feature name='md-clear'/>
      <feature name='stibp'/>
      <feature name='arch-capabilities'/>
      <feature name='ssbd'/>
      <feature name='xsaves'/>
      <feature name='pdpe1gb'/>
      <feature name='invtsc'/>
      <feature name='rdctl-no'/>
      <feature name='ibrs-all'/>
      <feature name='skip-l1dfl-vmentry'/>
      <feature name='mds-no'/>
      <feature name='pschange-mc-no'/>
      <feature name='tsx-ctrl'/>
      <pages unit='KiB' size='4'/>
      <pages unit='KiB' size='2048'/>
      <pages unit='KiB' size='1048576'/>
    </cpu>
    <power_management>
      <suspend_mem/>
    </power_management>
    <iommu support='no'/>
    <migration_features>
      <live/>
      <uri_transports>
        <uri_transport>tcp</uri_transport>
        <uri_transport>rdma</uri_transport>
      </uri_transports>
    </migration_features>
    <topology>
      <cells num='1'>
        <cell id='0'>
          <memory unit='KiB'>65587660</memory>
          <pages unit='KiB' size='4'>16396915</pages>
          <pages unit='KiB' size='2048'>0</pages>
          <pages unit='KiB' size='1048576'>0</pages>
          <distances>
            <sibling id='0' value='10'/>
          </distances>
          <cpus num='12'>
            <cpu id='0' socket_id='0' die_id='0' core_id='0' siblings='0,6'/>
            <cpu id='1' socket_id='0' die_id='0' core_id='1' siblings='1,7'/>
            <cpu id='2' socket_id='0' die_id='0' core_id='2' siblings='2,8'/>
            <cpu id='3' socket_id='0' die_id='0' core_id='3' siblings='3,9'/>
            <cpu id='4' socket_id='0' die_id='0' core_id='4' siblings='4,10'/>
            <cpu id='5' socket_id='0' die_id='0' core_id='5' siblings='5,11'/>
            <cpu id='6' socket_id='0' die_id='0' core_id='0' siblings='0,6'/>
            <cpu id='7' socket_id='0' die_id='0' core_id='1' siblings='1,7'/>
            <cpu id='8' socket_id='0' die_id='0' core_id='2' siblings='2,8'/>
            <cpu id='9' socket_id='0' die_id='0' core_id='3' siblings='3,9'/>
            <cpu id='10' socket_id='0' die_id='0' core_id='4' siblings='4,10'/>
            <cpu id='11' socket_id='0' die_id='0' core_id='5' siblings='5,11'/>
          </cpus>
        </cell>
      </cells>
    </topology>
    <cache>
      <bank id='0' level='3' type='both' size='12' unit='MiB' cpus='0-11'/>
    </cache>
    <secmodel>
      <model>apparmor</model>
      <doi>0</doi>
    </secmodel>
    <secmodel>
      <model>dac</model>
      <doi>0</doi>
      <baselabel type='kvm'>+455:+456</baselabel>
      <baselabel type='qemu'>+455:+456</baselabel>
    </secmodel>
  </host>

  <guest>
    <os_type>hvm</os_type>
    <arch name='i686'>
      <wordsize>32</wordsize>
      <emulator>/usr/bin/qemu-system-i386</emulator>
      <machine maxCpus='255'>pc-i440fx-5.2</machine>
      <machine canonical='pc-i440fx-5.2' maxCpus='255'>pc</machine>
      <machine maxCpus='288'>pc-q35-5.2</machine>
      <machine canonical='pc-q35-5.2' maxCpus='288'>q35</machine>
      <machine maxCpus='255'>pc-i440fx-2.12</machine>
      <machine maxCpus='255'>pc-i440fx-2.0</machine>
      <machine maxCpus='1'>xenpv</machine>
      <machine maxCpus='288'>pc-q35-4.2</machine>
      <machine maxCpus='255'>pc-i440fx-2.5</machine>
      <machine maxCpus='255'>pc-i440fx-4.2</machine>
      <machine maxCpus='255'>pc-i440fx-1.5</machine>
      <machine maxCpus='255'>pc-q35-2.7</machine>
      <machine maxCpus='255'>pc-i440fx-2.2</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.7</machine>
      <machine maxCpus='128'>xenfv-3.1</machine>
      <machine canonical='xenfv-3.1' maxCpus='128'>xenfv</machine>
      <machine maxCpus='255'>pc-q35-2.4</machine>
      <machine maxCpus='288'>pc-q35-2.10</machine>
      <machine maxCpus='255'>pc-i440fx-1.7</machine>
      <machine maxCpus='288'>pc-q35-5.1</machine>
      <machine maxCpus='288'>pc-q35-2.9</machine>
      <machine maxCpus='255'>pc-i440fx-2.11</machine>
      <machine maxCpus='288'>pc-q35-3.1</machine>
      <machine maxCpus='288'>pc-q35-4.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.4</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.3</machine>
      <machine maxCpus='255'>pc-i440fx-4.1</machine>
      <machine maxCpus='255'>pc-i440fx-5.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.9</machine>
      <machine maxCpus='1'>isapc</machine>
      <machine maxCpus='255'>pc-i440fx-1.4</machine>
      <machine maxCpus='255'>pc-q35-2.6</machine>
      <machine maxCpus='255'>pc-i440fx-3.1</machine>
      <machine maxCpus='288'>pc-q35-2.12</machine>
      <machine maxCpus='255'>pc-i440fx-2.1</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.0</machine>
      <machine maxCpus='288'>pc-q35-4.0.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.6</machine>
      <machine maxCpus='255'>pc-i440fx-1.6</machine>
      <machine maxCpus='288'>pc-q35-5.0</machine>
      <machine maxCpus='288'>pc-q35-2.8</machine>
      <machine maxCpus='255'>pc-i440fx-2.10</machine>
      <machine maxCpus='288'>pc-q35-3.0</machine>
      <machine maxCpus='288'>pc-q35-4.0</machine>
      <machine maxCpus='128'>xenfv-4.2</machine>
      <machine maxCpus='288'>microvm</machine>
      <machine maxCpus='255'>pc-i440fx-2.3</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.2</machine>
      <machine maxCpus='255'>pc-i440fx-4.0</machine>
      <machine maxCpus='255'>pc-i440fx-5.0</machine>
      <machine maxCpus='255'>pc-i440fx-2.8</machine>
      <machine maxCpus='255'>pc-q35-2.5</machine>
      <machine maxCpus='255'>pc-i440fx-3.0</machine>
      <machine maxCpus='288'>pc-q35-2.11</machine>
      <domain type='qemu'/>
      <domain type='kvm'/>
    </arch>
    <features>
      <pae/>
      <nonpae/>
      <acpi default='on' toggle='yes'/>
      <apic default='on' toggle='no'/>
      <cpuselection/>
      <deviceboot/>
      <disksnapshot default='on' toggle='no'/>
    </features>
  </guest>

  <guest>
    <os_type>hvm</os_type>
    <arch name='x86_64'>
      <wordsize>64</wordsize>
      <emulator>/usr/bin/qemu-system-x86_64</emulator>
      <machine maxCpus='255'>pc-i440fx-5.2</machine>
      <machine canonical='pc-i440fx-5.2' maxCpus='255'>pc</machine>
      <machine maxCpus='288'>pc-q35-5.2</machine>
      <machine canonical='pc-q35-5.2' maxCpus='288'>q35</machine>
      <machine maxCpus='255'>pc-i440fx-2.12</machine>
      <machine maxCpus='255'>pc-i440fx-2.0</machine>
      <machine maxCpus='1'>xenpv</machine>
      <machine maxCpus='288'>pc-q35-4.2</machine>
      <machine maxCpus='255'>pc-i440fx-2.5</machine>
      <machine maxCpus='255'>pc-i440fx-4.2</machine>
      <machine maxCpus='255'>pc-i440fx-1.5</machine>
      <machine maxCpus='255'>pc-q35-2.7</machine>
      <machine maxCpus='255'>pc-i440fx-2.2</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.7</machine>
      <machine maxCpus='128'>xenfv-3.1</machine>
      <machine canonical='xenfv-3.1' maxCpus='128'>xenfv</machine>
      <machine maxCpus='255'>pc-q35-2.4</machine>
      <machine maxCpus='288'>pc-q35-2.10</machine>
      <machine maxCpus='255'>pc-i440fx-1.7</machine>
      <machine maxCpus='288'>pc-q35-5.1</machine>
      <machine maxCpus='288'>pc-q35-2.9</machine>
      <machine maxCpus='255'>pc-i440fx-2.11</machine>
      <machine maxCpus='288'>pc-q35-3.1</machine>
      <machine maxCpus='288'>pc-q35-4.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.4</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.3</machine>
      <machine maxCpus='255'>pc-i440fx-4.1</machine>
      <machine maxCpus='255'>pc-i440fx-5.1</machine>
      <machine maxCpus='255'>pc-i440fx-2.9</machine>
      <machine maxCpus='1'>isapc</machine>
      <machine maxCpus='255'>pc-i440fx-1.4</machine>
      <machine maxCpus='255'>pc-q35-2.6</machine>
      <machine maxCpus='255'>pc-i440fx-3.1</machine>
      <machine maxCpus='288'>pc-q35-2.12</machine>
      <machine maxCpus='255'>pc-i440fx-2.1</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.0</machine>
      <machine maxCpus='255'>pc-i440fx-2.6</machine>
      <machine maxCpus='288'>pc-q35-4.0.1</machine>
      <machine maxCpus='255'>pc-i440fx-1.6</machine>
      <machine maxCpus='288'>pc-q35-5.0</machine>
      <machine maxCpus='288'>pc-q35-2.8</machine>
      <machine maxCpus='255'>pc-i440fx-2.10</machine>
      <machine maxCpus='288'>pc-q35-3.0</machine>
      <machine maxCpus='288'>pc-q35-4.0</machine>
      <machine maxCpus='128'>xenfv-4.2</machine>
      <machine maxCpus='288'>microvm</machine>
      <machine maxCpus='255'>pc-i440fx-2.3</machine>
      <machine maxCpus='255' deprecated='yes'>pc-1.2</machine>
      <machine maxCpus='255'>pc-i440fx-4.0</machine>
      <machine maxCpus='255'>pc-i440fx-5.0</machine>
      <machine maxCpus='255'>pc-i440fx-2.8</machine>
      <machine maxCpus='255'>pc-q35-2.5</machine>
      <machine maxCpus='255'>pc-i440fx-3.0</machine>
      <machine maxCpus='288'>pc-q35-2.11</machine>
      <domain type='qemu'/>
      <domain type='kvm'/>
    </arch>
    <features>
      <acpi default='on' toggle='yes'/>
      <apic default='on' toggle='no'/>
      <cpuselection/>
      <deviceboot/>
      <disksnapshot default='on' toggle='no'/>
    </features>
  </guest>

</capabilities>
"""

@pytest.mark.parametrize(
    'arch,res',
    [
      ('x86_64', '/usr/bin/qemu-system-x86_64'),
      ('amd64', '/usr/bin/qemu-system-x86_64'),
      ('i686', '/usr/bin/qemu-system-i386'),
    ]
)
def test_lookup_emulator(arch, res):
    path = util.lookup_emulator(capabilities_xml_text, arch)
    assert path == res

