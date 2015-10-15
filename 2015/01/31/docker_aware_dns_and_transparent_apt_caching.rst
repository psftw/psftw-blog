Docker-aware DNS and Transparent APT Caching
============================================

.. categories:: docker, devops

As part of collaborating on `Official Repositories <http://docs.docker.com/docker-hub/official_repos/>`_,
I wind up building a lot of Debian/Ubuntu-based Docker images.  The ``docker build``
cache is useful, though there are still situations in which downloading APT
packages repeatedly is unavoidable. With some DNS trickery and an APT proxy
cache, you can eliminate most of these redundant downloads and greatly speed up
your builds.

   **UPDATE 2015-07-12:** This trick no longer works, and I'm not interested in
   tracking down a solution as I've migrated to a new DNS setup.

-----

The secret sauce is `github.com/tianon/rawdns <https://github.com/tianon/rawdns>`_.
Go read that first!

Before we can fire up ``tianon/rawdns``, we need a configuration file:

.. code-block:: javascript

    {
      "http.debian.net.": {
        "type": "static",
        "cnames": [ "apt-cacher-ng.docker" ],
        "nameservers": [ "127.0.0.1" ]
      },
      "archive.ubuntu.com.": {
        "type": "static",
        "cnames": [ "apt-cacher-ng.docker" ],
        "nameservers": [ "127.0.0.1" ]
      },
      "docker.": {
        "type": "containers",
        "socket": "unix:///var/run/docker.sock"
      },
      ".": {
        "type": "forwarding",
        "nameservers": [ "8.8.8.8", "8.8.4.4" ]
      }
    }

In this example, a DNS request for ``http.debian.net`` or
``apt-cacher-ng.docker`` will both resolve to the IP of the named Docker
container ``apt-cacher-ng``.  Let's start our ``rawdns`` container and verify
that it can resolve itself.

.. code-block:: console

    $ docker run -d --restart=always --name rawdns \
          -p 53:53/udp -p 53:53/tcp \
          -v /var/run/docker.sock:/var/run/docker.sock \
          -v $(pwd)/rawdns.json:/etc/rawdns.json:ro \
          tianon/rawdns rawdns /etc/rawdns.json
    7f535b1322aacebd1d66cadafe71480140a7e9e2676b49a4b44cff51e4305f70
    $ dig @localhost rawdns.docker
    ; <<>> DiG 9.9.5-3ubuntu0.1-Ubuntu <<>> @localhost rawdns.docker
    ; (1 server found)
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 65120
    ;; flags: qr rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0
    ;; WARNING: recursion requested but not available

    ;; QUESTION SECTION:
    ;rawdns.docker.                 IN      A

    ;; ANSWER SECTION:
    rawdns.docker.          0       IN      A       172.17.0.7

    ;; Query time: 1 msec
    ;; SERVER: 127.0.0.1#53(127.0.0.1)
    ;; WHEN: Sat Jan 31 19:58:01 EST 2015
    ;; MSG SIZE  rcvd: 60

Next, add ``--dns 172.17.42.1`` to your Docker daemon options and restart it.
Verify that all containers can resolve each other and external sites properly.

.. code-block:: console

    $ docker run -it --rm ubuntu
    root@37dc7897e15b:/# ping rawdns.docker
    PING rawdns.docker (172.17.0.3) 56(84) bytes of data.
    64 bytes from 172.17.0.3: icmp_seq=1 ttl=64 time=0.124 ms
    ^C
    --- rawdns.docker ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 0.124/0.124/0.124/0.000 ms
    root@37dc7897e15b:/# ping google.com
    PING google.com (74.125.21.101) 56(84) bytes of data.
    64 bytes from yv-in-f101.1e100.net (74.125.21.101): icmp_seq=1 ttl=43 time=16.7 ms
    ^C
    --- google.com ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 16.734/16.734/16.734/0.000 ms

Finally, update your host system's resolver to ``localhost``.

For the actual ``apt-cacher-ng`` implementation, I borrowed from
`github.com/tianon/dockerfiles <https://github.com/tianon/dockerfiles>`_.

.. code-block:: console

    $ docker run -d --restart=always --name apt-cacher-ng \
          --dns 8.8.8.8 --dns 8.8.4.4 -v /var/cache/apt-cacher-ng \
          tianon/apt-cacher-ng

Notice that we specify our DNS explicitly so that this container will not be
redirected to itself when looking up the external ``http.debian.net`` or
``archive.ubuntu.com``.

Putting it all together, let's verify that we've actually sped up our Docker
builds.

.. code-block:: console

    $ docker run -it --rm debian:jessie
    root@f90d6f68ea14:/# apt-get update && time apt-get install -y vim dstat tcpdump ipcalc
    ...
    Fetched 20.6 MB in 28s (726 kB/s)
    ...
    real    0m39.099s
    user    0m8.125s
    sys     0m2.839s
    root@f90d6f68ea14:/# exit
    exit
    $ docker run -it --rm debian:jessie
    root@eeb1908139f8:/# apt-get update && time apt-get install -y vim dstat tcpdump ipcalc
    ...
    Fetched 20.6 MB in 0s (57.3 MB/s)
    ...
    real    0m10.555s
    user    0m6.967s
    sys     0m2.397s

The latest version of the scripts I'm using are available at
`github.com:psftw/docker-cache <https://github.com/psftw/docker-cache>`_.

