# Problematic key bindings
`meta-<key>meta-…` key bindings may conflict with vimode. For example, these
default key bindings are all considered problematic:

* `meta-jmeta-l` -> `/input jump_last_buffer`
* `meta-jmeta-r` -> `/server raw`
* `meta-jmeta-s` -> `/server jump`
* `meta-wmeta-meta2-A` -> `/window up`
* `meta-wmeta-meta2-B` -> `/window down`
* `meta-wmeta-meta2-C` -> `/window right`
* `meta-wmeta-meta2-D` -> `/window left`
* `meta-wmeta-b` -> `/window balance`
* `meta-wmeta-s` -> `/window swap`

This only matters after you press Esc. For example:

* Press `Esc` to switch to Normal mode.
* Press `w` expecting to move the cursor to the next word.
* `Esc-w` is actually detected as `meta-w` by your terminal (and therefore
WeeChat). However, `meta-w` matches the beginning of known keybindings, such
as `meta-wmeta-meta2-A`. This means WeeChat won't report that `meta-w` was
pressed just yet, and will wait for another keystroke to see if that still
matches a known keybinding.
* The result is that vimode won't know you pressed `w`. Once you press another
key (e.g. `w`), it'll then receive a `ww` press and ignore that (since it's
bound to nothing). You'll have to press `w` a third time for vimode to detect
it.

You have a few choices to solve this:

* Live with it if you consider it's not important enough.
* Remove the problematic key bindings entirely.
* Rebind the problematic key bindings to something that won't conflict. The
  following key bindings are used in vimode's Normal mode, so you can use them
  for consistency:
    * `ctrl-^` -> `/input jump_last_buffer`
    * `ctrl-Wh` -> `/window left`
    * `ctrl-Wj` -> `/window down`
    * `ctrl-Wk` -> `/window up`
    * `ctrl-Wl` -> `/window right`
    * `ctrl-W=` -> `/window balance`
    * `ctrl-Wx` -> `/window swap`

To remove the old key bindings and add these, copy/paste the following commands
in WeeChat:

    /key unbind meta-jmeta-l
    /key unbind meta-jmeta-r
    /key unbind meta-jmeta-s
    /key unbind meta-wmeta-meta2-A
    /key unbind meta-wmeta-meta2-B
    /key unbind meta-wmeta-meta2-C
    /key unbind meta-wmeta-meta2-D
    /key unbind meta-wmeta-b
    /key unbind meta-wmeta-s
    /key unbind ctrl-W
    /key bind ctrl-^ /input jump_last_buffer
    /key bind ctrl-Wh /window left
    /key bind ctrl-Wj /window down
    /key bind ctrl-Wk /window up
    /key bind ctrl-Wl /window right
    /key bind ctrl-W= /window balance
    /key bind ctrl-Wx /window swap
