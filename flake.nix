{
  description = "Data Science End-to-End Project";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

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
          python39Packages.pygments
        ];

        dev-packages = with pkgs; [
          texlab
          zathura
          wmctrl
        ];
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [ latex-packages dev-packages ];
        };
        
        packages = flake-utils.lib.flattenTree {
          report = with import nixpkgs { inherit system; }; stdenvNoCC.mkDerivation rec {
            name = "report.pdf";
            src = ./document;

            buildInputs = [
              latex-packages
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
