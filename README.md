# saraayllon.github.io
Academic website of Sara Ayllón — https://saraayllon.github.io

## How to update the site
1. Edit the page texts in `_source/pages/` (`index.md`, `publications.md`, `working-papers.md`,
   `projects.md`, `talks.md`, `media.md`). Simple formatting: `## Heading`, `- list item`,
   `**bold**`, `*italic*`, `[link text](https://...)`.
2. Put new PDFs in `files/` and link them as `[pdf](files/name.pdf)`.
3. Run `python _source/build.py` to regenerate the `.html` pages.
4. Commit and push; GitHub Pages publishes the site within a minute or two.

The design is in `style.css`; the menu, profile links and CV file name are at the top of `_source/build.py`.
