{
  extra-packages ? [],
}: ({
  lib,
  klayout,
  coreutils,
  devshell,
}: let
  prompt = ''\[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] '';
  packages =
    [
      klayout
      coreutils
    ]
    ++ extra-packages;
in
  devshell.mkShell {
    devshell.packages = packages;
    devshell.interactive.PS1 = {
      text = ''PS1="${prompt}"'';
    };
    motd = "";
  })
