const fs = require('fs');
const https = require('https');
const serve = require('koa-static');
const mount = require('koa-mount');
const Koa = require('koa');
const app = new Koa();

//const data = fs.readFileSync('app.html');

function doRequest(path) {
    return new Promise((resolve, reject) => {
        try {
            https.get(path, res => {
                resolve(res);
            });
        } catch (e) {
            reject(e);
        }
    });
}


app.use(async(ctx, next) => {
    await next();
    console.log(ctx.path);

    if (ctx.path.startsWith("/assets")) {
        if (!fs.existsSync(`.${ctx.path}`)) {
            console.log(`downloading resource: ${ctx.path}`);
            let file = fs.createWriteStream(`.${ctx.path}`);
            let resp = await doRequest(`https://discordapp.com${ctx.path}`);
            resp.pipe(file);
        }

        if (ctx.path.endsWith(".js"))
            ctx.type = 'application/javascript';
        else if (ctx.path.endsWith(".css"))
            ctx.type = 'text/css';
        else if (ctx.path.endsWith(".svg"))
            ctx.type = 'image/svg+xml';
        else if (ctx.path.endsWith(".png"))
            ctx.type = 'image/png';
        else if (ctx.path.endsWith(".jpg"))
            ctx.type = 'image/jpeg';
        else if (ctx.path.endsWith(".gif"))
            ctx.type = 'image/gif';
        else if (ctx.path.endsWith(".map")) {
            ctx.type = 'application/json';
            ctx.body = '{}';
            return;
        }
        ctx.body = fs.readFileSync(`.${ctx.path}`);
    } else if (ctx.path.startsWith("/discrod/")) {
        if (fs.existsSync(`.${ctx.path}`)) {
            ctx.type = 'application/javascript';
            ctx.body = fs.readFileSync(`.${ctx.path}`);
        }
    } else {
        ctx.type = 'text/html';
        //ctx.body = data;
        ctx.body = fs.readFileSync('./discrod/index.html');
    }
});

app.listen(4000);

console.log('server launched on port 4000');