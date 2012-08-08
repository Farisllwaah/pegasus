#!/bin/bash

set -e

# Size of image in GB
SIZE=2

# Password for tutorial user
PASSWORD="pegasus"


if ! [[ "$(cat /etc/redhat-release 2>/dev/null)" =~ "CentOS release 6" ]]; then
    echo "This script must be run on a CentOS 6 machine"
    exit 1
fi

if [ $(id -u) -ne 0 ]; then
    echo "This script must be run as user root so that it can mount loopback devices"
    exit 1
fi

if [ $(sestatus | grep enabled | wc -l) -ne 0 ]; then
    echo "Disable SELinux before running this script"
    exit 1
fi

if [ "X$(which qemu-img)" == "X" ]; then
    echo "qemu-img is required"
    exit 1
fi

if [ "X$(which losetup)" == "X" ]; then
    echo "losetup is required"
    exit 1
fi

if [ "X$(which mkfs.ext4)" == "X" ]; then
    echo "mkfs.ext4 is required"
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "Usage: $0 disk.img"
    exit 1
fi

raw=$1
if ! [[ "$raw" =~ ".img" ]]; then
    echo "Image name must end with .img: $raw"
    exit 1
fi

mnt=$PWD/${raw/.img/}

if [ -f "$raw" ]; then
    echo "$raw exists"
    exit 1
fi



echo "Creating $SIZE GB image..."
dd if=/dev/zero of=$raw bs=1M count=1 seek=$(((SIZE*1024)-1))



echo "Creating first loop device..."
loop0=$(losetup -f --show $raw)



echo "Partitioning image..."
! fdisk $loop0 <<END
n
p
1


a
1
w
END



echo "Creating second loop device..."
loop1=$(losetup -o 32256 -f --show $raw)



echo "Formatting partition 1..."
# For some reason this tries to create a file system that is too big unless you specify the number of blocks
mkfs.ext4 -L rootdisk -b 4096 $loop1 $(((SIZE*262144)-256))



echo "Mounting partition 1..."
mkdir -p $mnt
mount $loop1 $mnt



echo "Creating basic directory layout..."
mkdir -p $mnt/{proc,etc,dev,var/{cache,log,lock/rpm}}



echo "Creating devices..."
MAKEDEV -d $mnt/dev -x console null zero urandom random



echo "Mounting /proc file system"
mount -t proc none $mnt/proc



echo "Creating /etc/fstab..."
cat > $mnt/etc/fstab << EOF
LABEL=rootdisk     /         ext4    defaults        1 1
tmpfs              /dev/shm  tmpfs   defaults        0 0
devpts             /dev/pts  devpts  gid=5,mode=620  0 0
none               /proc     proc    defaults        0 0
none               /sys      sysfs   defaults        0 0
EOF



echo "Installing minimal base packages..."
yum -c yum.conf --installroot=$mnt/ -y install yum dhclient rsyslog openssh-server openssh-clients curl passwd kernel grub e2fsprogs rootfiles vim-minimal sudo perl
yum --installroot=$mnt/ -y clean all


echo "Creating /etc files..."
#/etc/hosts
echo '127.0.0.1 localhost.localdomain localhost' > $mnt/etc/hosts
cat > $mnt/etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DEVICE=eth0
ONBOOT=yes
BOOTPROTO=dhcp
EOF
touch $mnt/etc/resolv.conf
cat > $mnt/etc/sysconfig/network <<EOF
NETWORKING=yes
HOSTNAME=localhost.localdomain
EOF



echo "Installing grub..."

# Identify kernel and ramdisk
pushd $mnt/boot
KERNEL=$(ls vmlinuz-*)
RAMDISK=$(ls initramfs-*)
popd

# Create grub.conf
cat > $mnt/boot/grub/grub.conf <<EOF
default 0
timeout 0
splashimage=(hd0,0)/boot/grub/splash.xpm.gz
hiddenmenu
title CentOS
    root (hd0,0)
    kernel /boot/$KERNEL ro root=LABEL=rootdisk rd_NO_LUKS rd_NO_LVM rd_NO_MD rd_NO_DM LANG=en_US.UTF-8 KEYBOARDTYPE=pc KEYTABLE=us nomodeset quiet selinux=0
    initrd /boot/$RAMDISK
EOF

# Create menu.lst
pushd $mnt/boot/grub
ln -s ./grub.conf menu.lst
popd

# Install grub stages
cp /boot/grub/stage1 /boot/grub/e2fs_stage1_5 /boot/grub/stage2 $mnt/boot/grub

# Install grub to MBR
grub --device-map=/dev/null <<EOF
device (hd0) $raw
root (hd0,0)
setup (hd0)
EOF



echo "Installing Condor..."
cat > $mnt/etc/yum.repos.d/condor.repo <<END
[condor]
name=Condor
baseurl=http://www.cs.wisc.edu/condor/yum/stable/rhel6
enabled=1
gpgcheck=0
END

yum --installroot=$mnt install -y condor

echo "TRUST_UID_DOMAIN = True" >> $mnt/etc/condor/condor_config.local



echo "Installing Pegasus..."
cat > $mnt/etc/yum.repos.d/pegasus.repo <<END
[pegasus]
name=Pegasus
baseurl=http://download.pegasus.isi.edu/wms/download/rhel/6/\$basearch/
gpgcheck=0
enabled=1
END

yum --installroot=$mnt install -y pegasus



echo "Creating tutorial user..."

# Create the user, set the password, and generate an ssh key
chroot $mnt /bin/bash <<END
useradd tutorial
echo $PASSWORD | passwd --stdin tutorial

mkdir -p /home/tutorial/.ssh
chmod 0700 /home/tutorial/.ssh
ssh-keygen -t rsa -b 2048 -N "" -f /home/tutorial/.ssh/id_rsa
cp /home/tutorial/.ssh/id_rsa.pub /home/tutorial/.ssh/authorized_keys
chmod 0600 /home/tutorial/.ssh/authorized_keys

echo 'tutorial	ALL=(ALL) 	ALL' >> /etc/sudoers
END

# Copy tutorial files into tutorial user's home dir
if [ -d ../../doc/tutorial ]; then
    cp -R ../../doc/tutorial/* $mnt/home/tutorial/
    rm -rf $mnt/home/tutorial/.svn $mnt/home/tutorial/bin/.svn $mnt/home/tutorial/input/.svn
fi

chroot $mnt /bin/bash <<END
chown -R tutorial:tutorial /home/tutorial
END



echo "Cleaning up image..."
yum --installroot=$mnt/ -y clean all



echo "Unmounting partition 1..."
sync
umount $mnt/proc
umount $mnt
rmdir $mnt



echo "Deleting loop devices..."
losetup -d $loop1
losetup -d $loop0



echo "Creating vmdk..."
qemu-img convert -f raw -O vmdk $raw ${raw/.img/.vmdk}
