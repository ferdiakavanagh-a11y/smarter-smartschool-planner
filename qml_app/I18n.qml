pragma Singleton
import QtQml
import "Translations.js" as Translations
QtObject {
    property string language: "en"
    readonly property var locale: Qt.locale(language === "nl" ? "nl_BE" : "en_GB")
    function t(text) { return Translations.translate(String(text), language) }
    function p(en, nl) { return language === "nl" ? nl : en }
}
