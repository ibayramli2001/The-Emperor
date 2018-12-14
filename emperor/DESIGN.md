I have used Pset8 Finance source code as a basis for the implementation of this project. The program runs on the IDE server via Python (Flask library), SQLite database (same from the Finance), two CSS documents, many HTML templates, and JavaScript.

CSS.
Two seperate CSS files have been used during the process of implementation: homepage.css and styles.css stored in the static folder. Because the homepage is the most graphics-intensive part of the program (its CSS is bigger than the CSS of the entire document), I decided to separate its CSS file. While some of the visual effects used in this project are purely CSS (snow, homescreen button animation etc.), some of them are produced trhough both CSS and JavaScript ( stock search page button, homepage form appear/disappear etc.).

HTML.
I have added new HTML pages (transfer, changepassword, stockinfo etc.) to the templates folder left from finance and deleted some of them (quote, quoted, sell etc.) that became obsolete after implementation of my project.

JavaScript.
JavaScript has been extensively used throughout the webpage to produce all kinds of checks (password validation, form hide/show, button enable/disable based on user response) and visual effects.

JQuery.
Jquery has been used more frequently than pure JavaScript in the context of functions and element selections.

AJAX.
AJAX was one of the ways I retrieved data from the server and updated the content in the real time. While the table in the Stock Search page is both generated and updated via AJAX (because the rquired data exists in outside servers), the Stockinfo page table is built with the data passed in through Python to Jinja (because the data exists within our internal sources) and the Price column only is actively updated through interaction with the server.

SQL.
This is the same database left form finance where I store transaction history and the user data.

Python.
I have used Python to generate the Stockinfo table along with the percent return column (which required a formula based on previous transactions of the user stored in the SQL table). I also used Pandas and Plot.ly libraries to generate the interactive graph (graph function on helpers.py) on the stock info page. Please be aware that Plot.ly is a paid feature and I use its 100-request demo version. This means that after 100 requests are reached the graph will stop functioning, but I have many more tries left (~90). Also, the graph is tied to a throwaway plotly account with an activated api key.