.pragma library

function percent(entry) {
    if (typeof entry.score === 'number' && isFinite(entry.score) && typeof entry.maximum === 'number' && isFinite(entry.maximum) && entry.maximum > 0) {
        var ratio = entry.score / entry.maximum * 100;
        return isFinite(ratio) ? ratio : null;
    }
    var label = entry.percentText || (/%$/.test(entry.extra || '') ? entry.extra : entry.kind === 'summary' ? entry.title : '');
    label = String(label || '').trim();
    if (!/^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)\s*%?$/.test(label)) return null;
    var value = Number(label.replace(',', '.').replace(/\s*%$/, ''));
    return isFinite(value) ? value : null;
}

function category(entry) {
    var value = percent(entry);
    return value === null ? 'neutral' : value < 50 ? 'red' : value <= 70 ? 'yellow' : value <= 90 ? 'green' : 'blue';
}

function ink(entry, dark) {
    var colors = dark ? {red:'#F3A2A7',yellow:'#F6D97B',green:'#93D8AF',blue:'#9ACBFF',neutral:'#C6C8CB'}
                      : {red:'#B7343D',yellow:'#8A6700',green:'#267447',blue:'#286EAD',neutral:'#62666A'};
    return colors[category(entry)];
}

function fill(entry, dark) {
    var colors = dark ? {red:'#462C30',yellow:'#423B24',green:'#263F32',blue:'#283D54',neutral:'#34373A'}
                      : {red:'#FBE4E5',yellow:'#FFF3B0',green:'#DDF2E5',blue:'#DFEEFF',neutral:'#F0F1F2'};
    return colors[category(entry)];
}
