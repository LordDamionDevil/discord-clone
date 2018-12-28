'use strict';
!function(modules) {
  /**
   * @param {?} element
   * @return {?}
   */
  function push(element) {
    var moduleId;
    var prop;
    var s = element[0];
    var appliedUpdate = element[1];
    var options = element[2];
    /** @type {number} */
    var i = 0;
    /** @type {!Array} */
    var _sizeAnimateTimeStamps = [];
    for (; i < s.length; i++) {
      prop = s[i];
      if (state[prop]) {
        _sizeAnimateTimeStamps.push(state[prop][0]);
      }
      /** @type {number} */
      state[prop] = 0;
    }
    for (moduleId in appliedUpdate) {
      if (Object.prototype.hasOwnProperty.call(appliedUpdate, moduleId)) {
        modules[moduleId] = appliedUpdate[moduleId];
      }
    }
    if (addRemoveClassesPostDigest) {
      addRemoveClassesPostDigest(element);
    }
    for (; _sizeAnimateTimeStamps.length;) {
      _sizeAnimateTimeStamps.shift()();
    }
    return result.push.apply(result, options || []), resolve();
  }

  function resolve() {
    var value;
    var i = 0;
    for (; i < result.length; i++) {
      var data = result[i];
      var c = true;
      var index = 1;
      for (; index < data.length; index++) {
        var map = data[index];
        if (0 !== state[map]) {
          c = false;
        }
      }
      if (c) {
        result.splice(i--, 1);
        value = __webpack_require__(__webpack_require__.s = data[0]);
      }
    }
    return value;
  }

  function __webpack_require__(moduleId) {
    if (installedModules[moduleId]) {
      return installedModules[moduleId].exports;
    }
    var module = installedModules[moduleId] = {
      i : moduleId,
      l : false,
      exports : {}
    };
    return modules[moduleId].call(module.exports, module, module.exports, __webpack_require__), module.l = true, module.exports;
  }
  
  window.PATCHER_ENV.getModule = (id) => installedModules[id];
  
  window.PATCHER_ENV.replaceModule = (id, module) => {
	installedModules[id] = {
		i: id,
		l: true,
		exports: module
	};
  };
  
  var installedModules = {};
  var state = {
    199 : 0
  };

  var result = [];

  __webpack_require__.e = function(name) {
    var result = [];
    var e = state[name];
    if (0 !== e) {
      if (e) {
        result.push(e[2]);
      } else {
        var b = new Promise(function(a, new_state) {
          e = state[name] = [a, new_state];
        });
        result.push(e[2] = b);
        var callback;
        var el_head = document.getElementsByTagName("head")[0];
        var script = document.createElement("script");
        script.charset = "utf-8";
        script.timeout = 120;
		
        var scriptName = function(name) {
			return __webpack_require__.p + PATCHER_ENV.scripts[name] + ".js";
        }(name);
		
		try {
			var item = PATCHER_ENV.storage.getItem("patched_" + scriptName);
			if (item != null) {
				script.text = pako.inflate(item);
			} else {
				//console.log(scriptName);
				script.src = PATCHER_ENV.assetsEndpoint + scriptName.substring(8);
				//script.src = GLOBAL_ENV.ASSET_ENDPOINT + scriptName;
			}
		} catch (error) {
			console.log(error);
		}

        callback = function(value) {
          /** @type {null} */
          script.onerror = script.onload = null;
          clearTimeout(autoResumeTimer);
          var c = state[name];
          if (0 !== c) {
            if (c) {
              var n = value && ("load" === value.type ? "missing" : value.type);
              var request = value && value.target && value.target.src;
              /** @type {!Error} */
              var error = new Error("Loading chunk " + name + " failed.\n(" + n + ": " + request + ")");
              error.type = n;
              error.request = request;
              c[1](error);
            }
            state[name] = void 0;
          }
        };
        /** @type {number} */
        var autoResumeTimer = setTimeout(function() {
          callback({
            type : "timeout",
            target : script
          });
        }, 12e4);
        /** @type {function(!Object): undefined} */
        script.onerror = script.onload = callback;
        el_head.appendChild(script);
      }
    }
    return Promise.all(result);
  };
  /** @type {!Array} */
  __webpack_require__.m = modules;
  __webpack_require__.c = installedModules;
  /**
   * @param {!Function} exports
   * @param {string} name
   * @param {!Function} getter
   * @return {undefined}
   */
  __webpack_require__.d = function(exports, name, getter) {
    if (!__webpack_require__.o(exports, name)) {
      Object.defineProperty(exports, name, {
        enumerable : true,
        get : getter
      });
    }
  };
  /**
   * @param {!Object} x
   * @return {undefined}
   */
  __webpack_require__.r = function(x) {
    if ("undefined" != typeof Symbol && Symbol.toStringTag) {
      Object.defineProperty(x, Symbol.toStringTag, {
        value : "Module"
      });
    }
    Object.defineProperty(x, "__esModule", {
      value : true
    });
  };
  /**
   * @param {number} name
   * @param {number} version
   * @return {?}
   */
  __webpack_require__.t = function(name, version) {
    if (1 & version && (name = __webpack_require__(name)), 8 & version) {
      return name;
    }
    if (4 & version && "object" == typeof name && name && name.__esModule) {
      return name;
    }
    /** @type {!Object} */
    var d = Object.create(null);
    if (__webpack_require__.r(d), Object.defineProperty(d, "default", {
      enumerable : true,
      value : name
    }), 2 & version && "string" != typeof name) {
      var a;
      for (a in name) {
        __webpack_require__.d(d, a, function(nameProp) {
          return name[nameProp];
        }.bind(null, a));
      }
    }
    return d;
  };
  /**
   * @param {!Object} module
   * @return {?}
   */
  __webpack_require__.n = function(module) {
    /** @type {function(): ?} */
	//console.log(module);
    var getter = module && module.__esModule ? function() {
      return module.default;
    } : function() {
      return module;
    };
    return __webpack_require__.d(getter, "a", getter), getter;
  };
  /**
   * @param {!Function} object
   * @param {string} name
   * @return {?}
   */
  __webpack_require__.o = function(object, name) {
    return Object.prototype.hasOwnProperty.call(object, name);
  };
  /** @type {string} */
  __webpack_require__.p = "/assets/";
  /**
   * @param {?} err
   * @return {?}
   */
  __webpack_require__.oe = function(err) {
    throw console.error(err), err;
  };
  var p = window.webpackJsonp = window.webpackJsonp || [];
  var choiceParagraphElement = p.push.bind(p);
  /** @type {function(?): ?} */
  p.push = push;
  p = p.slice();
  /** @type {number} */
  var x = 0;
  for (; x < p.length; x++) {
    push(p[x]);
  }
  var addRemoveClassesPostDigest = choiceParagraphElement;
  resolve();
}([]);
