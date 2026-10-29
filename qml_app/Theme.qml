pragma Singleton
import QtQuick
QtObject {
    property var backdrop: null
    property string style: "clear"
    property string scheme: "light"
    property bool fancy: true
    property bool matched: false
    property bool reducedMotion: false
    property bool animatedBackground: true
    property bool highContrast: false
    property bool active: true
    property real glassLevel: 0
    property real refractionLevel: .5
    property int wallpaperIndex: 1
    property real textScale: 1
    readonly property bool dark: scheme === "dark" || (scheme === "auto" && Application.styleHints.colorScheme === Qt.Dark)
    readonly property bool clear: style === "clear"
    readonly property bool motion: !reducedMotion && active
    readonly property color blue: clear ? (dark ? "#69B8EF" : "#2F76B8") : (dark ? "#0A84FF" : "#007AFF")
    readonly property color purple: clear ? (dark ? "#A9A4DD" : "#5B58A8") : (dark ? "#BF5AF2" : "#AF52DE")
    readonly property color orange: clear ? (dark ? "#E2B66D" : "#BC6608") : (dark ? "#FF9F0A" : "#FF9500")
    readonly property color green: clear ? (dark ? "#8ED1A8" : "#277A4C") : (dark ? "#30D158" : "#34C759")
    readonly property color red: clear ? (dark ? "#EA8185" : "#C0392F") : (dark ? "#FF453A" : "#FF3B30")
    readonly property color teal: clear ? (dark ? "#7FD6EC" : "#1A7897") : (dark ? "#64D2FF" : "#5AC8FA")
    readonly property color pink: clear ? (dark ? "#A9BFDD" : "#FFFFFF") : (dark ? "#FF375F" : "#FF2D55")
    readonly property color bg: clear ? (dark ? "#09131D" : "#EDF3FA") : (dark ? "#000000" : "#f2f2f7")
    readonly property color elevated: clear ? (dark ? "#142031" : "#ffffff") : (dark ? "#1c1c1e" : "#ffffff")
    readonly property color text: clear ? (dark ? "#F4F6F8" : "#0B1626") : (dark ? "#ffffff" : "#000000")
    readonly property color secondary: highContrast ? text : clear ? (dark ? "#b8dce4ee" : "#c212243c") : (dark ? "#c7f0f0fa" : "#db1e1e28")
    readonly property color dock: "#182737"
    readonly property color badge: "#5e7289"
    readonly property color tertiary: highContrast ? text : dark ? "#b8becad8" : secondary
    readonly property color fill: dark ? "#52787880" : "#29787880"
    readonly property color separator: dark ? "#2e8ca5be" : "#243c3c43"
    readonly property color rim: highContrast ? text : dark ? "#47aabed2" : "#c0ffffff"
    readonly property real glassOpacity: highContrast ? 1 : (dark ? .38 : .16) + .30*glassLevel
    readonly property color surface: alpha(elevated, glassOpacity)
    function alpha(c, a) { return Qt.rgba(c.r,c.g,c.b,a) }
    function typeColor(kind) { return kind === "Toets" ? red : kind === "Taak" ? blue : purple }
    function badgeInk(kind) { return Qt.tint(text,alpha(typeColor(kind),.25)) }
}
