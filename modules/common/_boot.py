import rp2
import vfs
import machine  # noqa: F401


bdev = rp2.Flash()
try:
    fs = vfs.VfsLfs2(bdev, progsize=256)
    vfs.mount(fs, "/")
except OSError:
    vfs.VfsLfs2.mkfs(bdev, progsize=256)
    fs = vfs.VfsLfs2(bdev, progsize=256)
    vfs.mount(fs, "/")


del rp2, vfs, bdev, fs
