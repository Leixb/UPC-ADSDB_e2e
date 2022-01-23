{
  description = "Data Science End-to-End Project";

  inputs.utils = {
    url = "github:numtide/flake-utils";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  inputs.mach-nix.url = "github:DavHau/mach-nix";

  outputs = { self, nixpkgs, utils, mach-nix }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pyenv = mach-nix.lib."${system}".mkPython {
          requirements = (builtins.readFile ./requirements.txt) + ''
            python-lsp-server
            pygments
          '';
        };

        latex-packages = with pkgs; [
          (texlive.combine {
            inherit (texlive)
              scheme-medium
              framed
              titlesec
              cleveref
              multirow
              wrapfig
              tabu
              threeparttable
              threeparttablex
              makecell
              environ
              biblatex
              biber
              fvextra
              upquote
              catchfile
              xstring
              csquotes
              minted
              dejavu
              comment
              footmisc
              xltabular
              ltablex
              ;
          })
          which
        ];

        dev-packages = with pkgs; [
          texlab
          zathura
          wmctrl
        ];
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [ latex-packages dev-packages pyenv ];
        };
        
        packages = utils.lib.flattenTree {
          report = with import nixpkgs { inherit system; }; stdenvNoCC.mkDerivation rec {
            name = "report.pdf";
            src = ./document;

            buildInputs = [
              latex-packages
              pkgs.python39Packages.pygments
            ];

            TEXMFHOME="./cache";
            TEXMFVAR="./cache/var";
            SOURCE_DATE_EPOCH = toString self.lastModified;

            buildPhase = ''
              latexmk -lualatex -shell-escape 000-main.tex
            '';

            installPhase = ''
              mkdir -p $out
              mv *.pdf $out/${name}
            '';
          };
        };

        defaultPackage = self.packages.${system}.report;
      }
    );
}
