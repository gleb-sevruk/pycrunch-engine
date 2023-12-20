# front

## Project setup
Node version: This was compiled for node v8 and using Intel macbook
hence - configure node to use:
```
nvm install 8
nvm use 8
```
M1 is not supported here;

After building using npm run build
1. copy the `front/dist` folder to the `pycrunch/web-ui` folder;
2. remove *.js.map files from the dist folder

```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Run your tests
```
npm run test
```

### Lints and fixes files
```
npm run lint
```

### Run your unit tests
```
npm run test:unit
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
