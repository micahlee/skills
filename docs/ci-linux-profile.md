# Pinned Linux CI profile (AXON-2790)

The disposable executor accepts `profile: "linux"` alongside the existing
absolute `tart` and `tartHome` paths. Omitted profile preserves the original
Mac/Xcode behavior. Repository code cannot select an image or alter the limits.
The Linux image is pinned by digest in the executor and must already be the
only stopped OCI base in its own Tart home. It uses four CPUs and six GiB RAM.

Both profiles use the same host slot, power/pause checks, pinned Softnet helper,
private-network denial, exact owned-guest cleanup and secret-free host environment.
No mounts, clipboard, graphics or device passthrough are enabled. Linux changes
DNS only inside its disposable guest, requires a Linux kernel and never changes
an Xcode alias. No runner registration or paid admission is added here.

The Linux image's virtual disk is twenty GB; admission needs 45 GiB free after
the base is provisioned, preserving host reserve even for a full clone rewrite.
A physical host still needs at least 24 GiB RAM. Separate Tart homes prevent
mixing Mac and Linux image inventories while retaining one physical-host slot.

This adds a closed executor profile, not a qualified installed Linux runner.
Before enabling a host, measure actual base/clone allocation and boot/teardown,
verify public network access and private-network denial, run representative
portable qualification with the expected tools, and verify cleanup. Keep Apple
tests on the qualified Mac profile. No VM runs or consumes memory when idle.
