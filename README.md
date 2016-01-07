# Small Facebook Discussion Analysis Toolkit

This is a collection of tools to (semi-)automatically collect and analyze data from online discussions on Facebook groups and pages (see blog post ['Scraping data from Facebook groups and pages'](https://mkonrad.net/2015/12/23/scraping-data-from-facebook-groups-and-pages.html)). This means that posts and comments (including their hierarchical structure and some metadata) are collected using either the Facebook API for public groups and pages or by parsing Facebook's HTML files for closed groups and pages. The data is saved in a JSON format and can be used for different analyses. By now, only counting nouns in all the posts and comments in German language is supported.

## Collecting data

Data from open and closed groups and pages can be collected although the latter means more manual work.

### Data from public groups and pages via batch-querying the Facebook Graph API

Posts and comments from public groups and pages can be collected automatically using a set of PHP scripts located under *collect/php_automated_public/*. You need to deploy this on a webserver along with the the Facebook PHP SDK (you can use
[*composer*](https://getcomposer.org/)) and create a Facebook App via [*Facebook for Developers*](https://developers.facebook.com/). Then copy `conf.sample.php` to `conf.php` and fill in the respective configuration settings (Facebook App ID, App Secret, etc.). Also determine which groups and pages should be considered by specifying them in `$CONF_GROUP_IDS` and `$CONF_PAGE_IDS`.

After that, browse to the URL where you uploaded to scripts, log in via Facebook and let the scraping scripts do their work. It will take some time and you can view the progress if you follow the output of your webserver's error log. Also note that it will fail when the amount of data is too big. In such cases, try to repeat the process by using smaller time spans in the configuration options of the groups/pages to scrape.

### Data from closed groups and pages via manual screen scraping

Closed groups and pages cannot automatically be scraped using the Facebook Graph API. Hence the only way to collect the data from there is via parsing Facebooks HTML output. It is necessary to visit the respective groups/pages, expand all necessary posts/comments/discussions and save everything to an HTML file (e.g. in Firefox: *File > Save page as...*, select format *Complete website*). Then the HTML parser in *collect/manual_html* can be used for the exported HTML files:

```
./parse_fb_html_files.py <html-file1> [html-file2 ...] <output-json-file>
```

This will generated a JSON structure similar to the one produced by the automatic method.

## Analyzing data

The produced JSON files can be used for analyses by using scripts in the *analyze/* folder. So far, only counting nouns in all the posts and comments is supported. The script is configured for German language but can easily be adopted to other languages. The usage of the noun-counting script is as follows:

```
./analyze_noun_counts.py <json-file-1> [json-file-2 ...] <output-csv-file>
```

It takes the JSON data from the scraping scripts and outputs a CSV file with the format "label, noun, count". The basic approach on how the nouns are extracted is described [in this blog post](https://mkonrad.net/2015/12/13/extracting-german-nouns-with-python-using-pattern-library-and-libleipzig.html).

## Requirements

All Python scripts were tested under Python 2.7 and might run with other 2.x versions too. The noun counting script requires:

* [pattern.de](http://www.clips.ua.ac.be/pages/pattern-de) from the [Pattern library](https://pypi.python.org/pypi/Pattern/2.6)
* optionally [libleipzig](https://pypi.python.org/pypi/libleipzig/1.3) and [suds](https://pypi.python.org/pypi/suds/0.4)

The PHP scripts for scraping public pages and groups are written in PHP 5 and require the [Facebook PHP SDK v5](https://developers.facebook.com/docs/reference/php). It can be installed using [*composer*](https://getcomposer.org/).

## License

Under MIT License. See `LICENSE` file.

