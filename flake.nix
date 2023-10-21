{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    forAllSystems = function:
      builtins.mapAttrs
      (system: pkgs: function pkgs)
      nixpkgs.legacyPackages;
  in {
    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {
        packages = [
          pkgs.patchutils
          pkgs.pyright
          pkgs.gitAndTools.delta
          pkgs.git
          (
            pkgs.python3.withPackages (pyPkgs: [
              pyPkgs.black
            ])
          )
        ];
      };
    });
  };
}
