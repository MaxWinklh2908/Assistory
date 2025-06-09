# Update data.json
All the data of ingame entities is stored in the `data/data.json`. It is up to date to version 1.0. With newer version of **Satisfactory** the file might be outdated. This file can be created by [this fork](https://github.com/MaxWinklh2908/SatisfactoryTools/tree/release-1.0) of [SatisfactoryTools by greeeny](https://github.com/greeny/SatisfactoryTools). If you want to use the containerized version, use the branch `containerized-data-generation` and follow the installation steps:

1. Clone the [fork repo]((https://github.com/MaxWinklh2908/SatisfactoryTools/tree/release-1.0)), step into the repo folder (`cd SatisfactoryTools`) and follow the installation (or use Docker later)

1. Get the `Docs.json`: The file is located on the computer after installing Satisfactory. See this [wiki page](https://satisfactory.wiki.gg/wiki/Community_resources#Docs.json). Note that there are many versions of the `Docs.json` named differently for each language. Select the file with the desired language e.g. `en-US.json` and copy it to `data/Docs.json`.

1. Change the encoding of ``data/Docs.json`` to **utf-8** (see [this issue](https://github.com/greeny/SatisfactoryTools/issues/67))

1. Run the parseDocs command `yarn parseDocs` (or `docker run --rm -v $PWD/data:/app/data -v $PWD/bin:/app/bin statisfactory-tools:latest`)

1. Step into the repo folder of **Assistory** and use the adaptation script `scripts/adapt_data.py` with the path to the generated `data.json` from the previous step: `python3 scripts/adapt_data.py /path/to/SatisfactoryTools/data/data.json`. Warnings are no problem here

The file `data/data.json` should be updated now.