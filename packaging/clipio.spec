# PyInstaller recipe for the packaged Clipio app.
#   Windows / Linux: dist/Clipio-Setup(.exe) — one file that shows the setup window and installs
#                    the app (the onedir launcher rides inside it as payload/).
#   macOS:           dist/Clipio.app — the bundle; the release workflow wraps it in a disk image.
# Run from the project root:  python packaging/make_icon.py && pyinstaller packaging/clipio.spec
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
MAC, WIN = sys.platform == "darwin", sys.platform == "win32"
ICON = str(ROOT / "build" / "icon.png")
NAME = "Clipio" if (WIN or MAC) else "clipio"

# Qt parts Clipio never uses (keeps the download small)
UNUSED = ["QtQuick/Controls", "QtQuick/Dialogs", "QtQuick/Templates", "QtQuick/NativeStyle",
          "QtQuick/Pdf", "QtQuick/VirtualKeyboard", "QtQuick/Scene2D", "QtQuick/Scene3D",
          "QtQuick/Timeline", "QtQuick/tooling", "QtQuick/LocalStorage", "QtQuick/Particles",
          "QtQuick3D", "Qt3D", "QtCharts", "QtDataVisualization", "QtGraphs", "QtLocation",
          "QtPositioning", "QtMultimedia", "QtWebEngine", "QtWebView", "QtWebChannel",
          "QtWebSockets", "QtSensors", "QtTest", "QtRemoteObjects", "QtScxml", "QtTextToSpeech",
          "QtQml/XmlListModel", "QtQml/StateMachine", "QtQml/WorkerScript", "QtQuick/Layouts",
          "QtQuick/Shapes", "QtQuick/LocalStorage", "translations",
          "Qt6Pdf", "Qt6Quick3D", "Qt6QuickControls2", "Qt6QuickTemplates2", "Qt6QuickDialogs",
          "Qt6Charts", "Qt6Multimedia", "Qt6VirtualKeyboard", "Qt6Positioning", "Qt6Location",
          "Qt6WebEngine", "Qt6Sql", "Qt6Test", "Qt6Designer", "Qt6Help", "Qt6OpenGLWidgets",
          "Qt6ShaderTools", "Qt6Graphs", "Qt6Sensors", "Qt6SerialPort", "Qt6Bluetooth", "Qt6Nfc",
          "Qt6Concurrent", "Qt6Xml", "Qt6PrintSupport", "Qt6SpatialAudio", "Qt6TextToSpeech",
          "Qt6LabsStyleKit", "qml/Qt/labs", "QtWayland/Compositor", "QtQml/DesignSupport",
          "QtQuick/VectorImage", "plugins/qmltooling", "plugins/tls", "plugins/networkinformation",
          "platformthemes/libqgtk3", "platformthemes/libqxdgdesktopportal"]

# Linux system libraries the GTK theme plugin pulled in (the plugin is dropped above)
SYSTEM_DROP = ("libgtk-3", "libgdk-3", "libgdk_pixbuf", "libglycin", "libcairo", "libpango", "libatk",
               "libatspi", "libcloudproviders", "libtinysparql", "libjson-glib", "libicu", "libxml2",
               "libepoxy", "libharfbuzz-subset", "libseccomp", "librsvg", "libfribidi", "libpixman",
               "libthai", "libdatrie", "libXcomposite", "libXdamage", "libXrandr", "libXinerama",
               "libXcursor", "libXfixes", "libwayland-egl", "libcolord", "liblcms2", "libjpeg", "libtiff")


# Drop every file whose path mentions an unused Qt part, and the system libraries listed above
def trim(toc):
    keep = []
    for e in toc:
        name = e[0].replace("\\", "/")
        if any(u in name for u in UNUSED):
            continue
        if "/" not in name and name.startswith(SYSTEM_DROP):
            continue
        keep.append(e)
    return keep


a = Analysis(
    [str(ROOT / "packaging" / "entry.py")],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / "clipio" / "ui"), "clipio/ui")],
    hiddenimports=["clipio.app", "clipio.panel", "clipio.setup.window", "PySide6.QtSvg",
                   *(["pynput.keyboard._darwin", "pynput.mouse._darwin"] if MAC else []),
                   *(["Xlib.ext.xtest"] if not (WIN or MAC) else [])],
    excludes=["tkinter", "unittest", "pydoc", "PySide6.QtNetworkAuth", "PySide6.QtSql",
              "PySide6.QtTest", "PySide6.QtConcurrent", "PySide6.QtXml", "PySide6.QtPrintSupport",
              "PySide6.QtOpenGLWidgets", "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtUiTools"],
    noarchive=False,
)
a.binaries = trim(a.binaries)
a.datas = trim(a.datas)
pyz = PYZ(a.pure)

# the onedir app: what ends up installed
app_exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NAME, console=False,
              icon=ICON, upx=False, argv_emulation=False,
              bundle_identifier="io.github.ardazeybek.clipio" if MAC else None)

if MAC:
    coll = COLLECT(app_exe, a.binaries, a.datas, name="Clipio")
    app = BUNDLE(coll, name="Clipio.app", icon=ICON, bundle_identifier="io.github.ardazeybek.clipio",
                 info_plist={"CFBundleName": "Clipio", "CFBundleDisplayName": "Clipio",
                             "CFBundleShortVersionString": open(ROOT / "clipio" / "__init__.py").read()
                             .split('__version__ = "')[1].split('"')[0],
                             "LSUIElement": True, "NSHighResolutionCapable": True,
                             "NSAppleEventsUsageDescription": "Clipio pastes the item you pick into the app you were using."})
else:
    # the setup file: the same app files plus the onedir launcher as payload/
    payload = [(f"payload/{Path(app_exe.name).name}", app_exe.name, "DATA")]
    setup = EXE(pyz, a.scripts, a.binaries, a.datas + payload, [],
                name="Clipio-Setup" if WIN else "Clipio-Setup-Linux", console=False,
                icon=ICON, upx=False, runtime_tmpdir=None)
