import os
import rp2
import vfs
import machine  # noqa: F401


# Try to mount the filesystem, and format the flash if it doesn't exist.

USER_FLASH_SIZE = rp2.Flash().ioctl(4, 0) * rp2.Flash().ioctl(5, 0)
LFS_SIZE = 1024 * 1024  # 1MB root filesystem
FS_LABEL = os.uname().machine.split(" ")[1]


bdev_lfs = rp2.Flash(start=USER_FLASH_SIZE - LFS_SIZE, len=LFS_SIZE)
try:
    lfs = os.VfsLfs2(bdev_lfs, progsize=256)
    vfs.mount(lfs, "/")
    os.listdir("/") # might fail with UnicodeError on corrupt FAT
except:  # noqa: E722
    os.VfsLfs2.mkfs(bdev_lfs, progsize=256)
    lfs = os.VfsLfs2(bdev_lfs, progsize=256)
    vfs.mount(lfs, "/")

bdev = rp2.Flash(start=0, len=USER_FLASH_SIZE - LFS_SIZE)
try:
    fat = vfs.VfsFat(bdev)
    fat.label(FS_LABEL)
    vfs.mount(fat, "/system", readonly=True)
    os.listdir("/system") # might fail with UnicodeError on corrupt FAT

except:  # noqa: E722
    import rp2
    from badgeware import fatal_error

    CACHE_FILE = "/.fsbackup"
    CACHE_SIZE = 16 * 1024
    BLOCK_SIZE = 4096

    USER_FLASH_SIZE = rp2.Flash().ioctl(4, 0) * rp2.Flash().ioctl(5, 0)
    LFS_SIZE = 1024 * 1024  # 1MB root filesystem

    buffer = bytearray(BLOCK_SIZE)


    bdev = rp2.Flash(start=0, len=USER_FLASH_SIZE - LFS_SIZE)

    try:
        with open(CACHE_FILE, "rb") as f:
            for block in range(CACHE_SIZE / BLOCK_SIZE):
                f.readinto(buffer)
                bdev.writeblocks(block, buffer)
        fatal_error("System Error!", "Unable to mount filesystem. Restored FAT from backup!")

    except OSError:
        fatal_error("System Error!", "Unable to mount filesystem. Uh, not much I can do here sorry! Please re-flash your board.")
    # vfs.VfsFat.mkfs(bdev)
    # fat = vfs.VfsFat(bdev)
    # fat.label(FS_LABEL)
    # vfs.mount(fat, "/system", readonly=True)

del os, vfs, bdev, bdev_lfs, fat, lfs
