(window.webpackJsonp=window.webpackJsonp||[]).push([[168],{5950:function(e,t,n){"use strict";t.__esModule=!0;var o,r=(o="function"==typeof Symbol&&Symbol.for&&Symbol.for("react.element")||60103,function(e,t,n,r){var a=e&&e.defaultProps,i=arguments.length-3;if(t||0===i||(t={}),t&&a)for(var s in a)void 0===t[s]&&(t[s]=a[s]);else t||(t=a||{});if(1===i)t.children=r;else if(i>1){for(var l=Array(i),u=0;u<i;u++)l[u]=arguments[u+3];t.children=l}return{$$typeof:o,type:e,key:void 0===n?null:""+n,ref:null,props:t,_owner:null}}),a=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var o in n)Object.prototype.hasOwnProperty.call(n,o)&&(e[o]=n[o])}return e},i=function(e){if(e&&e.__esModule)return e;var t={};if(null!=e)for(var n in e)Object.prototype.hasOwnProperty.call(e,n)&&(t[n]=e[n]);return t.default=e,t}(n(1)),s=h(n(9)),l=h(n(165)),u=h(n(43)),f=h(n(95)),d=h(n(6)),c=h(n(296)),p=h(n(546)),v=n(0),m=n(524),y=h(n(5576));function h(e){return e&&e.__esModule?e:{default:e}}function g(e,t){if(!e)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!t||"object"!=typeof t&&"function"!=typeof t?e:t}var C=function(e){function t(){var n,o;!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t);for(var r=arguments.length,a=Array(r),i=0;i<r;i++)a[i]=arguments[i];return n=o=g(this,e.call.apply(e,[this].concat(a))),o.state={verifying:!0,verified:!1},o.getType=function(){return o.props.match.params.type},o.isPopout=function(){return null!=window.opener},o.handleDone=function(){o.isPopout()&&window.close()},g(o,n)}return function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function, not "+typeof t);e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,enumerable:!1,writable:!0,configurable:!0}}),t&&(Object.setPrototypeOf?Object.setPrototypeOf(e,t):e.__proto__=t)}(t,e),t.prototype.componentDidMount=function(){var e=this,t=(0,m.parse)(this.props.location.search),n=t.code,o=t.state,r=t.oauth_verifier;if(null==t.loading){null!=r&&(n=r);var i=void 0;Object.keys(t).forEach(function(e){e.startsWith("openid.")&&(null==i&&(i={}),i[e]=t[e])});var s=function(t){var n=t.status;e.setState({verifying:!1,verified:204===n},function(){return e.state.verified&&e.handleDone()})},l={code:n,openid_params:i,state:o},u=function(t){return c.default.callback(e.getType(),l,t).then(s,s)};this.isPopout()?u(!1):p.default.request(v.RPCCommands.CONNECTIONS_CALLBACK,a({},l,{providerType:this.getType()})).then(s,function(e){return u("RPCError"!==e.name)}).then(function(){return p.default.disconnect()})}},t.prototype.render=function(){var e=this.state,t=e.verifying,n=e.verified,o=f.default.get(this.getType()),a=void 0;a=t?r("div",{className:y.default.message},void 0,d.default.Messages.CONNECTED_ACCOUNT_VERIFYING.format({name:o.name})):n?r("div",{className:y.default.message},void 0,d.default.Messages.CONNECTED_ACCOUNT_VERIFY_SUCCESS.format({name:o.name})):r("div",{className:(0,s.default)(y.default.message,y.default.error)},void 0,d.default.Messages.CONNECTED_ACCOUNT_VERIFY_FAILURE.format({name:o.name}));var i=void 0;return(this.isPopout()||t)&&(i=r(u.default,{className:y.default.btn,disabled:t,onClick:this.handleDone},void 0,t?r(l.default,{itemClassName:y.default.spinnerItem}):d.default.Messages.DONE)),r("div",{className:y.default.verifyConnectedAccount},void 0,r("div",{},void 0,r("div",{className:y.default.logos},void 0,r("div",{className:(0,s.default)(y.default.logo,y.default.logoDiscord)}),r("div",{className:y.default.logosDivider}),r("div",{className:y.default.logo,style:{backgroundImage:'url("'+o.icon.white+'")'}})),a,i))},t}(i.Component);C.displayName="VerifyConnectedAccount",t.default=C,e.exports=t.default}}]);
//# sourceMappingURL=55c7f935e65c4c53277c.js.map