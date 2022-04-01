# GtkStressTesting (GST)
GST is a GTK system utility designed to stress and monitor various hardware components like CPU and RAM.

## 💡 Features
<img src="/data/icons/hicolor/48x48@2x/apps/com.leinardi.gst.png" width="96" align="right" hspace="0" />

* Run different CPU and memory stress tests
* Run multi and single core benchmark
* Show Processor information (name, cores, threads, family, model, stepping, flags,bugs, etc)
* Show Processor's cache information
* Show Motherboard information (vendor, model, bios version, bios date, etc)
* Show RAM information (size, speed, rank, manufacturer, part number, etc)
* Show CPU usage (core %, user %, load avg, etc)
* Show Memory usage
* Show CPU's physical's core clock (current, min, max) 
* Show Hardware monitor (info provided by `sys/class/hwmon`)
<img src="/art/screenshot-1.png" width="800" align="middle"/>

## 📦 How to get GST
### Install from Flathub
This is the preferred way to get GST on any major distribution (Arch, Fedora, Linux Mint, openSUSE, Ubuntu, etc).

If you don't have Flatpak installed you can find step by step instructions [here](https://flatpak.org/setup/).

Make sure to have the Flathub remote added to the current user:

```bash
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

#### Install
```bash
flatpak --user install flathub com.leinardi.gst
```

#### Run
```bash
flatpak run com.leinardi.gst
```
### Distro specific packages
#### Arch Linux
Install the `gst` package from the AUR using your favourite helper, for example `yay -S gst`.

#### Fedora
[Official repo](https://src.fedoraproject.org/rpms/gst): `sudo dnf install gst`


### Install from source code
#### Build time dependencies
| Distro                | pkg-config         | Python 3.6+ | gobject-introspection       | meson | ninja-build | appstream-util |
| --------------------- | ------------------ | ----------- | --------------------------- | ----- | ----------- | -------------- |
| Arch Linux            | pkg-config         | python      | gobject-introspection       | meson | ninja       | appstream-glib |
| Fedora                | pkgconf-pkg-config | python3     | gobject-introspection-devel | meson | ninja-build | appstream-util |
| Ubuntu                | pkg-config         | python3     | libgirepository1.0-dev      | meson | ninja-build | appstream-util |

#### Run time dependencies
| Distro                | Python 3.6+ | pip         | gobject-introspection       | lm-sensors | stress-ng | dmidecode | python3-cairo |
| --------------------- | ----------- | ----------- | --------------------------- | ---------- | --------- | --------- | --------- |
| Arch Linux            | python      | python-pip  | gobject-introspection       | lm-sensors | stress-ng | dmidecode | python-cairo |
| Fedora                | python3     | python3-pip | gobject-introspection-devel | lm-sensors | stress-ng | dmidecode | python3-cairo-devel |
| Ubuntu                | python3     | python3-pip | libgirepository1.0-dev      | lm-sensors | stress-ng | dmidecode | python3-cairo-dev |

plus all the Python dependencies listed in [requirements.txt](requirements.txt)

#### Clone project and install
If you have not installed GST yet:
```bash
git clone --recurse-submodules -j4 https://gitlab.com/leinardi/gst.git
cd gst
git checkout release
sudo -H pip3 install -r requirements.txt
meson . build --prefix /usr
ninja -v -C build
sudo ninja -v -C build install
```

#### Update old installation
If you installed GST from source code previously and you want to update it:
```bash
cd gst
git fetch
git checkout release
git reset --hard origin/release
git submodule init
git submodule update
sudo -H pip3 install -r requirements.txt
meson . build --prefix /usr
ninja -v -C build
sudo ninja -v -C build install
```

#### Run
Once installed, to start it you can simply execute on a terminal:
```bash
gst
```

## ℹ️ TODO

- [ ] Preselect first used RAM bank
- [ ] Add RAM specific stress tests
- [ ] Get a better icon


## ⌨️ Command line options

  | Parameter                 | Description                               | Source | Flatpak |
  |---------------------------|-------------------------------------------|:------:|:-------:|
  |-v, --version              |Show the app version                       |    x   |    x    |
  |--debug                    |Show debug messages                        |    x   |    x    |
  |--autostart-on             |Enable automatic start of the app on login |    x   |         |
  |--autostart-off            |Disable automatic start of the app on login|    x   |         |

## 🖥️ Build, install and run with Flatpak
If you don't have Flatpak installed you can find step by step instructions [here](https://flatpak.org/setup/).

Make sure to have the Flathub remote added to the current user:

```bash
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Clone the repo
```bash
git clone --recurse-submodules -j4 https://gitlab.com/leinardi/gst.git
```
It is possible to build the local source or the remote one (the same that Flathub uses)
### Local repository
```bash
./build.sh --flatpak-local --flatpak-install
```
### Remote repository
```bash
./build.sh --flatpak-remote --flatpak-install
```
### Run
```bash
flatpak run com.leinardi.gst --debug
```

## ❓ FAQ

### The Flatpak version of GST is not using my theme, how can I fix it?
To fix this issue install a Gtk theme from Flathub. This way, Flatpak applications will automatically pick the 
installed Gtk theme and use that instead of Adwaita.

Use this command to get a list of all the available Gtk themes on Flathub:
```bash
flatpak --user remote-ls flathub | grep org.gtk.Gtk3theme
```
And then just install your preferred theme. For example, to install Yaru:
```
flatpak install flathub org.gtk.Gtk3theme.Yaru
```

### Where are the settings and profiles stored on the filesystem?
| Installation type |                     Location                     |
|-------------------|:------------------------------------------------:|
| Flatpak           |        `$HOME/.var/app/com.leinardi.gst/`        |
| Source code       | `$XDG_CONFIG_HOME` (usually `$HOME/.config/gst`) |

## 💚 How to help the project
### Discord server
If you want to help testing or developing it would be easier to get in touch using the discord server of the project: https://discord.gg/wjBH8w3  
Just write a message on the general channel saying how you want to help (test, dev, etc) and quoting @leinardi. If you don't use discor but still want to help just open a new issue here.


### Can I support this project some other way?

Something simple that everyone can do is to star it on both [GitLab](https://gitlab.com/leinardi/gst) and [GitHub](https://github.com/leinardi/gst).
Feedback is always welcome: if you found a bug or would like to suggest a feature,
feel free to open an issue on the [issue tracker](https://gitlab.com/leinardi/gst/issues).

## ℹ️ Acknowledgements
Thanks to:

 - Colin Ian King for the [stress-ng](https://kernel.ubuntu.com/git/cking/stress-ng.git/) CLI tool
 - @999eagle for maintaining the [AUR package](https://aur.archlinux.org/packages/gst/)
 - @tim74 for maintaining the [Fedora package](https://src.fedoraproject.org/rpms/gst)
 - all the people that helped testing and reported bugs

## 📰 Media coverage 
 - [GamingOnLinux](https://www.gamingonlinux.com/articles/monitor-and-stress-test-your-linux-gaming-pc-with-gtkstresstesting.15854) 🇬🇧
 - [OMG! Ubuntu! 🇬](https://www.omgubuntu.co.uk/2020/01/new-stress-test-linux-app) 🇬🇧
 - [lffl](https://www.lffl.org/2020/01/gtkstresstesting-gst-tool.html) 🇮🇹
 - [Świat Linuksa](https://www.youtube.com/watch?v=F0_giDR9pI4) 📺 🇵🇱
 - [Manuel Cabrera Caballero](https://www.youtube.com/watch?v=Hh04ffSa7P0) 📺 🇪🇸
 - [Diolinux](https://www.diolinux.com.br/2020/01/faca-teste-de-stress-no-linux-com-o-gtkstresstesting.html) 🇧🇷
 - [Cerebrux](https://cerebrux.net/2020/01/29/gtkstresstesting-%CF%80%CE%B1%CF%81%CE%B1%CE%BA%CE%BF%CE%BB%CE%BF%CF%8D%CE%B8%CE%B7%CF%83%CE%B7-stress-test-cpu-ram/) 🇬🇷


## 📝 License
```
This file is part of gst.

Copyright (c) 2020 Roberto Leinardi

gst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

gst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with gst.  If not, see <http://www.gnu.org/licenses/>.
```