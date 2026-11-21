// fit.js — writes the picture height into <body data-h> so render.sh can size the screenshot exactly
document.fonts.ready.then(() => { document.body.dataset.h = Math.ceil(document.body.getBoundingClientRect().height); });
