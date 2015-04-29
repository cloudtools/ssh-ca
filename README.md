New Project Announcement
========================

We figured out how to make this service a bit more self-service and arguably more secure. That project is here:

https://github.com/cloudtools/ssh-cert-authority


Certificate based SSH
=====================

"*One key to rule them all, One key to find them,  
One key to bring them all and in the cloud bind them*"

Certificate based SSH allows us to launch a server at time X and grant
SSH access to that server later at time X + Y without touching the
authorized keys file. Further it allows us to generate certificates that
expire at some predefined time meaning that users can be granted access
to a system for a short period of time.

The primary use case is:

  Jane the Engineer needs shell access to a machine running in
  production in order to help debug a problem. In general Jane does not
  need access to these machines and it is expected that she only needs
  access for a few hours at which point her access should automatically
  be revoked.

A second use case is around host keys:

  A server is launched into the cloud by an adminstrator and made
  available to other users over SSH. The first time a user connects to
  that machine she is prompted to inspect the host key fingerprint and
  type either "yes" or "no". Most users blindly type yes. By signing a
  host key and generating a certificate users can blindly accept any
  server that presents a valid certificate as trustworthy and never be
  prompted to blindly type "yes" again.

Quick start
===========

User keys
---------

Generate a certificate authority (yep, this is exactly like making an ordinary private key):

`ssh-keygen -f ~/.ssh/ssh_ca_production -b 4096`

Put the CA's public key on the remote host of your choosing into
`authorized_keys`, but prefix it with cert-authority:

`echo "cert-authority $(cat ssh_ca_production.pub)" >> ~/.ssh/authorized_keys`

Generate a certificate using the utility in this github repo:

`sign_key -e production -u user@example.com -p ~/.ssh/id_rsa.pub -t +1d`

Install the certificate using the other utility in this github repo:

`get_cert '<output from sign_key command>'`

SSH like normal.

Host keys
---------

First create a CA using ssh-keygen as described in the previous section.
Then use the `sign_host_key` script included in this distribution.

This script will SSH out to the remote server and:

  - Copy back the host's public key
  - Sign it (it will ask you for the passphrase to your CA
  - Copy it back to the host
  - Restart sshd

Once the cert is in place you need to have your client computers told to
trust the CA. Take the public portion of your CA and add it into your
`authorized_keys` file according to this format:

  `@cert-authority *.domain ssh-rsa ...`

The `*.domain` is intended to be the domain you're signing keys for. If
you were working with a CA that only signed host keys for veznat.com you
could enter `*.veznat.com`. If you sign keys for all sorts of domains
you can enter a `*` here without any qualification, however, you should
understand what this means in the context of a compromised CA before
doing so.

Usage
=====

If you're running this command you must already have access to the
root-ca certificate. Despite being really well encrypted this file is
kept secret and you'll need to pass the "I require access to this file"
test in order to get a copy.

Once you've got the CA file you can use the script here. Usage is found
with the --help option (not documented here to avoid duplicating the
code).

When running this script a number of things happen:

- An entry is made in an audit log in S3 to document that the key was
  made, for who, by who and how long the key is valid.
- A serial number is incremented and stored in S3. This makes revoking
  certificates later a lot easier.
- The generated certificate is stored in S3 and a temporary (2 hour) URL
  is generated for the user to download the certificate

If a user's public key is given as an argument to the script it is also
uploaded to S3 effectively caching it for the next time the script is
used for that user. Without a public key filename being passed in the
script attempts to load the key from S3.

How it works
============

The CA owner creates a new certificate authority keypair. This is just a
generic 4096 bit RSA keypair that could be used for regular old SSH
authentication.  However, we will protect the generated private key with our
lives (and a really great 2-factor passphrase).

```
cd ~/.ssh
ssh-keygen -f ssh_ca_production -b 4096
```

We take the public key portion of that key pair and add it to the
authorized_keys file of machines we want to login to. However, unlike
normal, the line in authorized_keys is prefixed with `cert-authority`.

```
echo "cert-authority $(cat ssh_ca_production.pub)" >> ~/.ssh/authorized_keys
```

At this point the server is ready to accept authentication using any
private key that can also present a certifcate that was signed using the
root-ca's private key.

We now get the users public key and sign it with the CA key. The below command
specifies the S3 bucket (-b), S3 region (-r), environment (-e), user name (-u),
users public key file (-p) and how long before the key expires (-t).

```
sign_key -b my-s3-bucket -r us-west-1 -e production -u user@example.com -p user-example.pub -t +1d
```

The output of this is an S3 URL that you give to the user. The user will now
run `get_key` to download the generated certificate from S3 and install it
into their ~/.ssh directory. Note the quotes around the download link.

```
get_key 'https://my-s3-bucket.s3-us-west-1.amazonaws.com/certs/user%40example.com-cert.pub?Signature=neidfJ5bZ5YbmAi2ouJVZzZzZz%3D&Expires=1391025703&AWSAccessKeyId=AKIAJ7HFYKZIVF3ZZZZ'
```

The user can now log into the remote system using these new keys.

`get_key` is nothing particularly fancy. It simply downloads the
certificate and attempts to find the corresponding private key for the
user and places the cert next to it. OpenSSH requires that the cert be
named similarly to the private key. For example, if your private key is
named `id_rsa` the cert must be in a file named `id_rsa-cert.pub`. It
really does simply append `-cert.pub` to the filename.

Troubleshooting
===============

Typical problems include not having the certificate added to the running
ssh-agent. You can list certificates and keys with the ssh-add command:
`ssh-add -l`. You should see the certificate listed:

```
2048 66:b5:be:e5:7e:09:3f:98:97:36:9b:64:ec:ea:3a:fe .ssh/id_rsa (RSA)
2048 66:b5:be:e5:7e:09:3f:98:97:36:9b:64:ec:ea:3a:fe .ssh/id_rsa (RSA-CERT)
```
If you don't see it listed simply run `ssh-add <path to private key>` again.

Incompatibilities and Annoyances
================================

OpenSSH - One cert per key
--------------------------
You can only have one SSH cert loaded per private key at any one time
(The SSH agent works by loading your private key file `keyfile` and then
looks for a certificate in a file named `keyfile`-cert.pub.

If, like us, you have multiple environments that you want to access in a
short time window the best workaround is to have multiple private keys.
This project has builtin support for per-environment keys. To take
advantage of this upload your private key, using the sign_key command,
but specifying your username in the format
`user?environment=THE-ENVIRONMENT`. For example, I might use
`bob@veznat.com?environment=stage` for staging and
`bob@veznat.com?environment=prod` for production. The public keys that
are being uploaded her must correspond to separate private keys
otherwise when get_cert runs it will not be able to reliably figure out
where to put the downloaded cert.

If you use this multiple environment naming trick in your username you
do not need to specify anything special when running sign_key in the
future. Sign key searches for your public key first by doing an
environment specific lookup and second looking for a generic one.

Vagrant
-------
When a user has one of these cert keys in their keychain
[vagrant](http://www.vagrantup.com/) will hang in bringing up a new box.
This is due to an incompatibility in the Ruby net-ssh package included in
vagrant. This is being tracked in this
[net-ssh issue](https://github.com/net-ssh/net-ssh/pull/142).

OS X
----
OS X's magic ssh-add (the one where it prompts you in the GUI of OS X
for your passphrase) does not properly add the certificate. In order to
utilize certificates you'll want to `ssh-add .ssh/my_private_key` at a
terminal in order for the certificate to properly be added to your
ssh-agent.


