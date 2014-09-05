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
* Rebind the problematic key bindings to something that won't conflict.

To remove the conflicting key bindings and add recommended key bindings,
you can run the `/vimode bind_keys` command inside WeeChat. To only list
changes, run `/vimode bind_keys --list` instead.

# Esc key not being detected instantly
This can happen if you're using a terminal multiplexer, such as tmux or screen.
You can decrease (or remove) the time your multiplexer waits to determine
input key sequences to fix this.

* tmux: set `escape-time` to 0 (e.g. `tmux set-option escape-time 0`, or add
`set -sg escape-time 0` to your `.tmux.conf` file).
* screen: set `maptimeout` to 0 (e.g. `C-a :` followed by `maptimeout 0`, or
add `maptimeout 0` to your `.screenrc`).
