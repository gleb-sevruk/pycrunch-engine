module.exports.api_url = 'http://127.0.0.1:53734'
// module.exports.api_url = 'http://0.0.0.0:51570'

// inside aiohttp server
let target_url = window.location.protocol + "//" + window.location.hostname + (window.location.port ? ':' + window.location.port: '');
console.log('url: ' + target_url)
module.exports.api_url = target_url
