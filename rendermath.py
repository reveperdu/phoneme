html_template = r"""
<!DOCTYPE html>
<html>

<head>
    <link rel="stylesheet" href="javascript/katex/katex.min.css">
    <script src="javascript/katex/katex.min.js"></script>
</head>

<body>
    <textarea id="content" style="width:30em;height:3em">[PLACEHOLDER]</textarea><br>
    <button onclick="rendermath()">render</button>
    <p id="output"></p>
    <!--if script is placed in head, it will be unable to find element-->
    <script>
        function rendermathStr(text) {
            return text.replace(/\$\$([\s\S]*?)\$\$|\$([\s\S]*?)\$/g, (full, block, inline) => {
                if (block) {
                    return katex.renderToString(block, { displayMode: true, throwOnError: false });
                }
                else {
                    return katex.renderToString(inline, { displayMode: false, throwOnError: false });
                }
            })
        }
        function rendermath() {
            eContent = document.getElementById("content")
            eOutput = document.getElementById("output")
            eOutput.innerHTML = rendermathStr(eContent.value)
        }

        rendermath()
    </script>
</body>

</html>
"""

default_math = r"default: $$\frac{\partial u}{\partial t}+u\frac{\partial u}{\partial x}=\frac{\partial^2 u}{\partial x^2}$$"


def render_math(text: str = default_math):
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


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    render_math(default_math)
    app.exec()
