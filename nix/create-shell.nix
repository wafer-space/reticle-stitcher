{
  extra-packages ? [],
}: ({
  lib,
  klayout-app,
  coreutils,
  python3,
  devshell,
}: let
  python-env = (
    python3.withPackages (
      pp:
      (
        [python3.pkgs.klayout]
      )
    )
  );
  python-env-sitepackages = "${python-env}/${python-env.sitePackages}";
  prompt = ''\[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] '';
  packages =
    [
      python-env
    
      klayout-app
      coreutils
    ]
    ++ extra-packages;
in
  devshell.mkShell {
    devshell.packages = packages;
    env = [
      {
        name = "NIX_PYTHONPATH";
        value = "${python-env-sitepackages}";
      }
    ];
    devshell.interactive.PS1 = {
      text = ''PS1="${prompt}"'';
    };
    motd = "";
  })
