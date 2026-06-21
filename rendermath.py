html_template = r"""
<!DOCTYPE html>
<html>

<head>
    <link rel="stylesheet" href="javascript/katex/katex.min.css">
    <script src="javascript/katex/katex.min.js"></script>
</head>
<body>
    <p id="content">[PLACEHOLDER]</p>
    <!--if script is placed in head, it will be unable to find element-->
    <script>
        function rendermath(text) {
            return text.replace(/\$\$([\s\S]*?)\$\$|\$([\s\S]*?)\$/g, (full, block, inline) => {
                if (block) {
                    return katex.renderToString(block, { displayMode: true, throwOnError: false });
                }
                else {
                    return katex.renderToString(inline, { displayMode: false, throwOnError: false });
                }
            })
        }
        e=document.getElementById("content")
        e.innerHTML=rendermath(e.innerHTML)
    </script>
</body>
</html>
"""


def render_math(text: str):
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtCore import QUrl

    # is view deleted at Qt side after closing the window? if not, maybe it is unnecessary
    # to create window in each call
    # without "global view", view will be released after function return?
    global view
    view = QWebEngineView()
    html = html_template.replace("[PLACEHOLDER]", text)
    # without some tweaking webview seems to be unable to access local files
    view.setHtml(html, QUrl.fromLocalFile("/usr/share/"))
    view.show()
