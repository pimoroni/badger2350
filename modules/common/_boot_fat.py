import os
import rp2
import vfs
import machine  # noqa: F401
import powman


# Try to mount the filesystem, and format the flash if it doesn't exist.

USER_FLASH_SIZE = rp2.Flash().ioctl(4, 0) * rp2.Flash().ioctl(5, 0)
LFS_SIZE = 256 * 1024  # 256k state filesystem
FS_LABEL = os.uname().machine.split(" ")[1]

bdev = rp2.Flash(start=0, len=USER_FLASH_SIZE - LFS_SIZE)
try:
    fat = vfs.VfsFat(bdev)
    fat.label(FS_LABEL)
    vfs.mount(fat, "/")
    os.listdir("/") # might fail with UnicodeError on corrupt FAT

except:  # noqa: E722
    vfs.VfsFat.mkfs(bdev)
    fat = vfs.VfsFat(bdev)
    fat.label(FS_LABEL)
    vfs.mount(fat, "/")

bdev_lfs = rp2.Flash(start=USER_FLASH_SIZE - LFS_SIZE, len=LFS_SIZE)
try:
    lfs = os.VfsLfs2(bdev_lfs, progsize=256)
    vfs.mount(lfs, "/state")
except:  # noqa: E722
    os.VfsLfs2.mkfs(bdev_lfs, progsize=256)
    lfs = os.VfsLfs2(bdev_lfs, progsize=256)
    vfs.mount(lfs, "/state")

if powman.get_wake_reason() == powman.WAKE_DOUBLETAP:
    import _msc  # noqa: F401
    rp2.enable_msc()

del os, vfs, bdev, bdev_lfs, fat, lfs
