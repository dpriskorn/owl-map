module.exports = {
    "env": {
        "browser": true,
        "es6": true
    },
    "extends": [
        "eslint:recommended",
        "plugin:vue/essential"
    ],
    "globals": {
        "Atomics": "readonly",
        "SharedArrayBuffer": "readonly"
    },
    "parserOptions": {
        "ecmaVersion": 14,
        "sourceType": "module"
    },
    "plugins": [
        "vue"
    ],
    "rules": {
        "max-lines": ["error", {"max": 700, "skipBlankLines": true, "skipComments": true}]
    }
};
