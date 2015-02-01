Simplifying the Workflow
===================================

.. categories:: devops

Recently I've applied some `DevOps <https://en.wikipedia.org/wiki/DevOps>`_
ideas to my software development workflow.  With the help of virtualization and
Ansible, I was able to create a basic CentOS6 and Python2.7 configuration
management template.

.. more::

Goals
------------

* Avoid OS noise; stick to CentOS6

* Have the freedom to micromanage software versions as needed, though hopefully
  others will do most of the work for me

* Utilize configuration management and server orchestration for smooth
  deployments

* Work with disposable VM snapshots

* Avoid adding too much complexity in the name of simplification

The rest of this document is a high level walk-through of how I've achieved
some of these goals so far.

VM setup
------------

*Kids, don't try this at home.*

Create a new VM disk image.

.. code-block:: console

    $ qemu-img create -f qcow2 centos64base.img 10G
    Formatting 'centos64base.img', fmt=qcow2 size=10737418240 encryption=off
    cluster_size=65536 lazy_refcounts=off

Create a basic KVM start script.

.. literalinclude:: /_static/vm-centos64
   :language: bash

Install CentOS6.4

.. image:: /_static/centos6welcome.png

Setup networking - The VM should have access to the internet, and be accessible
via SSH over the host-guest port forward.

Setup pubkey authentication as root

.. code-block:: console

    $ scp -P 5022 ~/.ssh/id_rsa.pub root@localhost:~/
    root@localhost's password:
    $ ssh -p 5022 root@localhost
    root@localhost's password:
    Last login: Wed May 15 21:26:24 2013 from 10.0.2.2
    # mkdir .ssh
    # cat id_rsa.pub >> .ssh/authorized_keys
    # chmod 700 .ssh
    # chmod 600 .ssh/authorized_keys
    # exit
    $ ssh -p 5022 root@localhost
    Last login: Wed May 15 21:31:28 2013 from 10.0.2.2

Shutdown the VM.

At this point we have a bare bones functional CentOS6.4 VM, so take a snapshot.

.. code-block:: console

    $ qemu-img snapshot -c base centos64base.img
    $ qemu-img info centos64base.img
    image: /home/peter/120g/images/centos64base.img
    file format: qcow2
    virtual size: 10G (10737418240 bytes)
    disk size: 936M
    cluster_size: 65536
    Snapshot list:
    ID        TAG                 VM SIZE                DATE       VM CLOCK
    1         base                      0 2013-05-15 16:21:13   00:00:00.000

From here, we can iterate using qcow2 snapshots.

CentOS6 and Repositories
------------------------

CentOS6 was chosen because it is a stable target that receives security
updates.  It also has a decent packaging system based on ``rpm`` which makes
for relatively easy management.

Out of the box, the available packages for CentOS6.4 are a little spotty, so
additional repositories are needed to fill the gaps.

* The `EPEL <http://fedoraproject.org/wiki/EPEL>`_ repository provides a
  massive (8,700+) set of packages.

* The `PUIAS <http://springdale.math.ias.edu/>`_ Computational repository
  provides a ``python27`` package and some common libraries which can be
  installed independently of the system's ``python`` ecosystem.

Rather than log in to the VM and manually add these repositories, it is a good
time to bring configuration management in to the mix to avoid this kind of
tedium.

Ansible
----------

The current mainstream tools in the "configuration management" space (primarily
`Puppet <https://puppetlabs.com/>`_ and `Chef <http://www.opscode.com/chef/>`_)
didn't impress me.  Neither did the lower level libraries such as `Fabric
<http://docs.fabfile.org>`_.  I wanted something simple, hackable, at the right
level of abstraction, and with batteries included.  `Salt
<http://saltstack.com/community.html>`_ seemed like a solid contender at first,
but ultimately the need for master/slave daemons felt icky.  I plan to take a
second look at these tools, but for now, I've been having fun with `Ansible
<http://ansible.cc/>`_.

Ansible is a new tool for managing systems based on ``sshd`` and Python 2.4+.
The `README <https://github.com/ansible/ansible/blob/devel/README.md>`_
explains it better than I could.

Bootstrapping a Development VM
-------------------------------

So far we have created a "base" CentOS6.4 VM snapshot and discussed the use of
``rpm`` and Ansible.  Now let's apply our tools to create a Python2.7
development environment.  This section describes my first baby steps with
Ansible; the latest "playbooks" are tracked at `github:psftw/simple-ansible
<https://github.com/psftw/simple-ansible>`_.

Create a hosts file to define the connection to our VM

**hosts**

.. code-block:: ini

    [vm-dev]
    localhost ansible_ssh_port=5022

Verify we can reach the ``vm-dev`` system with Ansible

.. code-block:: console

    $ ansible vm-dev -m ping -u root
    localhost | success >> {
        "changed": false,
        "ping": "pong"
    }

Create a "common" role, which installs EPEL, ``vim``, and ``dstat``.

**roles/common/tasks/main.yml**

.. code-block:: yaml

    ---

    - name: Add EPEL repository
      copy: src=epel.repo dest=/etc/yum.repos.d/epel.repo

    - name: Add EPEL GPG KEY
      copy: src=RPM-GPG-KEY-EPEL-6 dest=/etc/pki/rpm-gpg

    - name: Install basic tools
      yum: name={{ item }} state=latest
      with_items:
      - vim
      - dstat

Include relevant static files

.. code-block:: console

    $ ll roles/common/files/
    total 24K
    -rw-r--r-- 1 peter peter  957 May 15 22:50 epel.repo
    -rw-r--r-- 1 peter peter 1.7K May 15 22:34 RPM-GPG-KEY-EPEL-6

Create a "python" role, which installs PUIAS, ``python27`` and some additional
libraries.

**roles/python/tasks/main.yml**

.. code-block:: yaml

    ---

    - name: Add PUIAS repository
      copy: src=puias.repo dest=/etc/yum.repos.d/puias.repo

    - name: Add PUIAS GPG KEY
      copy: src=RPM-GPG-KEY-puias dest=/etc/pki/rpm-gpg

    - name: Install python27 and friends
      yum: name={{ item }} state=latest
      with_items:
      - python27
      - python27-devel
      - python27-imaging
      - python27-matplotlib
      - python27-nose
      - python27-pygments
      - python27-tools
      - graphviz-python27

Create a top-level playbook to apply these roles to our VM

**vm-dev.yml**

.. code-block:: yaml

    ---
    # bootstrap a dev vm

    - hosts: vm-dev
      gather_facts: no
      user: root
      roles:
      - role: common
      - role: python

Execute the playbook (after turning off the Cowsay "feature")

.. code-block:: console

    $ ansible-playbook vm-dev.yml

    PLAY [vm-dev] *****************************************************************

    TASK: [Add EPEL repository] ***************************************************
    ok: [localhost]

    TASK: [Add EPEL GPG KEY] ******************************************************
    ok: [localhost]

    TASK: [Install basic tools] ***************************************************
    ok: [localhost] => (item=vim,dstat)

    TASK: [Add PUIAS repository] **************************************************
    ok: [localhost]

    TASK: [Add PUIAS GPG KEY] *****************************************************
    ok: [localhost]

    TASK: [Install python27 and friends] ******************************************
    ok: [localhost] =>
    (item=python27,python27-devel,python27-imaging,python27-matplotlib,python27-nose,python27-pygments,python27-tools,graphviz-python27)

    PLAY RECAP ********************************************************************
    localhost                  : ok=6    changed=0    unreachable=0    failed=0

Since I had already applied this configuration to the system, Ansible didn't
need to make any changes.

Verify ``python2.7`` in our VM:

.. code-block:: pycon

    Python 2.7.3 (default, Mar 11 2013, 22:38:13)
    [GCC 4.4.7 20120313 (Red Hat 4.4.7-3)] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import PIL, matplotlib, nose, pygments, gv
    >>>

Redistributing ``rpm``
--------------------------------------------

1. Obtain some  ``rpm`` files.  *Optionally --resign them.*
2. Run ``createrepo`` to generate repository metadata
3. Configure yum to use the repository

This is useful when you want to distribute original ``rpm`` packages, or you
need to push to servers that don't have internet access.

