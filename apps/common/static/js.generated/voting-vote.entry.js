!function(modules) {
    function __webpack_require__(moduleId) {
        if (installedModules[moduleId]) return installedModules[moduleId].exports;
        var module = installedModules[moduleId] = {
            i: moduleId,
            l: !1,
            exports: {}
        };
        return modules[moduleId].call(module.exports, module, module.exports, __webpack_require__), 
        module.l = !0, module.exports;
    }
    var installedModules = {};
    __webpack_require__.m = modules, __webpack_require__.c = installedModules, __webpack_require__.i = function(value) {
        return value;
    }, __webpack_require__.d = function(exports, name, getter) {
        __webpack_require__.o(exports, name) || Object.defineProperty(exports, name, {
            configurable: !1,
            enumerable: !0,
            get: getter
        });
    }, __webpack_require__.n = function(module) {
        var getter = module && module.__esModule ? function() {
            return module.default;
        } : function() {
            return module;
        };
        return __webpack_require__.d(getter, "a", getter), getter;
    }, __webpack_require__.o = function(object, property) {
        return Object.prototype.hasOwnProperty.call(object, property);
    }, __webpack_require__.p = "", __webpack_require__(__webpack_require__.s = 27);
}([ function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    function template(id) {
        var element = __WEBPACK_IMPORTED_MODULE_0_jquery___default()(id);
        if (!element.length) throw "Can't find template '" + id + "'.";
        if (element.length > 1) throw "More then 1 template '" + id + "' found.";
        return element[0].outerHTML;
    }
    function error_handler(response) {
        console.error(response);
        var message = void 0;
        message = response.responseJSON && response.responseJSON[0] ? response.responseJSON[0] : response.responseJSON && response.responseJSON.error ? response.responseJSON.error : response.responseJSON && response.responseJSON.message ? response.responseJSON.message : response.responseJSON && response.responseJSON.detail ? response.responseJSON.detail : response.responseJSON && response.responseJSON.non_field_errors ? response.responseJSON.non_field_errors[0] : response.statusText, 
        swal(trans.error, message, "error");
    }
    function request(url, method, data) {
        method = method || "GET";
        var request = {
            url: url,
            method: method
        };
        return "POST" === method || "PATCH" === method || "PUT" === method ? (request.data = JSON.stringify(data), 
        request.contentType = "application/json") : data && console.error("data is not empty and method is not POST|PATCH|PUT"), 
        __WEBPACK_IMPORTED_MODULE_0_jquery___default.a.ajax(request);
    }
    function deep_copy(object) {
        return __WEBPACK_IMPORTED_MODULE_0_jquery___default.a.extend(!0, {}, object);
    }
    __webpack_require__.d(__webpack_exports__, "b", function() {
        return delimiters;
    }), __webpack_require__.d(__webpack_exports__, "d", function() {
        return urls;
    }), __webpack_require__.d(__webpack_exports__, "g", function() {
        return trans;
    }), __webpack_require__.d(__webpack_exports__, "h", function() {
        return is_admin;
    }), __webpack_exports__.a = template, __webpack_exports__.e = error_handler, __webpack_exports__.c = request, 
    __webpack_exports__.f = deep_copy;
    var __WEBPACK_IMPORTED_MODULE_0_jquery__ = __webpack_require__(6), __WEBPACK_IMPORTED_MODULE_0_jquery___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_jquery__), delimiters = [ "${", "}" ], urls = window.urls, trans = window.trans, is_admin = window.is_admin;
}, function(module, exports) {
    module.exports = Vue;
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    __webpack_exports__.a = {
        props: {
            error: null
        },
        template: '<span class="k-widget k-tooltip k-tooltip-validation k-invalid-msg" role="alert" v-show="error"><span class="k-icon k-warning"></span> {{ error && error.join("; ") }}</span>'
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    __webpack_require__.d(__webpack_exports__, "a", function() {
        return VOTING_TYPE;
    }), __webpack_require__.d(__webpack_exports__, "b", function() {
        return FAA_CHOICES;
    }), __webpack_require__.d(__webpack_exports__, "c", function() {
        return UrlMaker;
    });
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), VOTING_TYPE = {
        YES_NO: 1,
        SINGLE_SELECT: 2,
        MULTIPLE_SELECT: 3,
        ELECTION: 4,
        FOR_AGAINST_ABSTAIN: 5
    }, FAA_CHOICES = {
        FOR_: 1,
        AGAINST: 2,
        ABSTAIN: 3
    }, UrlMaker = {
        make_voting_url: function(voting_id) {
            return __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_detail.replace("9999", voting_id);
        },
        make_question_url: function(question) {
            return question.id ? __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_questions_detail.replace("1111", question.voting).replace("2222", question.id) : __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_questions.replace("1111", question.voting);
        },
        make_voter_url: function(voter) {
            return voter.id ? __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_voters_detail.replace("1111", voter.voting).replace("2222", voter.id) : __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_voters.replace("1111", voter.voting);
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    function datetime_filter(value) {
        if (value) return moment(value).format("MMM DD, YYYY h:mm a");
    }
    function nl2br(value) {
        return value && value.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br/>\n");
    }
    __webpack_exports__.b = datetime_filter, __webpack_exports__.a = nl2br;
}, function(module, exports) {
    module.exports = VueRouter;
}, function(module, exports) {
    module.exports = jQuery;
}, , , , , function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    Object.defineProperty(__webpack_exports__, "__esModule", {
        value: !0
    });
    var __WEBPACK_IMPORTED_MODULE_0_vue_router__ = __webpack_require__(5), __WEBPACK_IMPORTED_MODULE_0_vue_router___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_vue_router__), __WEBPACK_IMPORTED_MODULE_1_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_1_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vue__), __WEBPACK_IMPORTED_MODULE_2__voting_vote_views_VoteMainView__ = __webpack_require__(15), __WEBPACK_IMPORTED_MODULE_3__common_filters__ = __webpack_require__(4), routes = [ {
        path: "/",
        component: __WEBPACK_IMPORTED_MODULE_2__voting_vote_views_VoteMainView__.a,
        props: {
            all: !1
        }
    }, {
        path: "/*",
        redirect: "/"
    } ], router = new __WEBPACK_IMPORTED_MODULE_0_vue_router___default.a({
        routes: routes
    });
    __WEBPACK_IMPORTED_MODULE_1_vue___default.a.filter("nl2br", __WEBPACK_IMPORTED_MODULE_3__common_filters__.a), 
    new __WEBPACK_IMPORTED_MODULE_1_vue___default.a({
        router: router
    }).$mount("#app");
}, , , , function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    function _classCallCheck(instance, Constructor) {
        if (!(instance instanceof Constructor)) throw new TypeError("Cannot call a class as a function");
    }
    function _possibleConstructorReturn(self, call) {
        if (!self) throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
        return !call || "object" != typeof call && "function" != typeof call ? self : call;
    }
    function _inherits(subClass, superClass) {
        if ("function" != typeof superClass && null !== superClass) throw new TypeError("Super expression must either be null or a function, not " + typeof superClass);
        subClass.prototype = Object.create(superClass && superClass.prototype, {
            constructor: {
                value: subClass,
                enumerable: !1,
                writable: !0,
                configurable: !0
            }
        }), superClass && (Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass);
    }
    __webpack_require__.d(__webpack_exports__, "a", function() {
        return VoteMainView;
    });
    var _dec, _class, __WEBPACK_IMPORTED_MODULE_0_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_0_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_vue__), __WEBPACK_IMPORTED_MODULE_1_vue_class_component__ = __webpack_require__(24), __WEBPACK_IMPORTED_MODULE_1_vue_class_component___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vue_class_component__), __WEBPACK_IMPORTED_MODULE_2__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_3__voting_common__ = __webpack_require__(3), __WEBPACK_IMPORTED_MODULE_4__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_5_vue_focus__ = __webpack_require__(25), _createClass = (__webpack_require__.n(__WEBPACK_IMPORTED_MODULE_5_vue_focus__), 
    function() {
        function defineProperties(target, props) {
            for (var i = 0; i < props.length; i++) {
                var descriptor = props[i];
                descriptor.enumerable = descriptor.enumerable || !1, descriptor.configurable = !0, 
                "value" in descriptor && (descriptor.writable = !0), Object.defineProperty(target, descriptor.key, descriptor);
            }
        }
        return function(Constructor, protoProps, staticProps) {
            return protoProps && defineProperties(Constructor.prototype, protoProps), staticProps && defineProperties(Constructor, staticProps), 
            Constructor;
        };
    }()), VoteMainView = (_dec = __WEBPACK_IMPORTED_MODULE_1_vue_class_component___default()({
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.a)("#main-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_2__common_utils__.b,
        components: {
            Errors: __WEBPACK_IMPORTED_MODULE_4__common_components_Errors__.a
        },
        directives: {
            focus: __WEBPACK_IMPORTED_MODULE_5_vue_focus__.focus
        }
    }))(_class = function(_Vue) {
        function VoteMainView() {
            var _ref, _temp, _this, _ret;
            _classCallCheck(this, VoteMainView);
            for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) args[_key] = arguments[_key];
            return _temp = _this = _possibleConstructorReturn(this, (_ref = VoteMainView.__proto__ || Object.getPrototypeOf(VoteMainView)).call.apply(_ref, [ this ].concat(args))), 
            _this.voting = null, _this.voter_key = window.voter_key, _this.current_question_index = null, 
            _this.VOTING_TYPE = __WEBPACK_IMPORTED_MODULE_3__voting_common__.a, _this.FAA_CHOICES = __WEBPACK_IMPORTED_MODULE_3__voting_common__.b, 
            _this.answer = null, _this.errors = {}, _this.show_vote_note = !1, _ret = _temp, 
            _possibleConstructorReturn(_this, _ret);
        }
        return _inherits(VoteMainView, _Vue), _createClass(VoteMainView, [ {
            key: "update_voting",
            value: function() {
                var _this2 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_2__common_utils__.d.vote_voting_details).then(function(voting) {
                    _this2.voting = voting, null === _this2.current_question_index && _this2._select_first_unanswered_question(voting);
                }, __WEBPACK_IMPORTED_MODULE_2__common_utils__.e);
            }
        }, {
            key: "post_answer",
            value: function() {
                var _this3 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_2__common_utils__.d.vote_voting_details, "PUT", this.answer).then(function(updated_voting) {
                    _this3.voting = updated_voting, _this3.current_question_index + 1 < updated_voting.questions.length ? (_this3.current_question_index += 1, 
                    _this3._update_answer()) : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_2__common_utils__.d.vote_voting_mark_done, "POST", {}).then(function(done) {
                        return _this3.voting = done;
                    }, __WEBPACK_IMPORTED_MODULE_2__common_utils__.e);
                }, function(error) {
                    400 === error.status ? _this3.errors = error.responseJSON : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.e)(error);
                });
            }
        }, {
            key: "previous_question",
            value: function() {
                this.current_question_index -= 1, this._update_answer();
            }
        }, {
            key: "toggle_vote_note",
            value: function() {
                this.show_vote_note ? (this.show_vote_note = !1, this.answer.vote_note = null) : this.show_vote_note = !0;
            }
        }, {
            key: "_update_answer",
            value: function() {
                this.voting.answers[this.question.id] ? this.answer = __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_2__common_utils__.f)(this.voting.answers[this.question.id]) : this.answer = {
                    question: this.question.id,
                    yes_no: null,
                    answers: [],
                    candidate: null
                }, this.show_vote_note = !!this.answer.vote_note;
            }
        }, {
            key: "_select_first_unanswered_question",
            value: function(voting) {
                var _this4 = this, answers = {};
                for (var i in voting.answers) answers[voting.answers[i].question] = !0;
                voting.questions.some(function(question, index) {
                    if (!answers[question.id]) return _this4.current_question_index = index, !0;
                }), this._update_answer();
            }
        }, {
            key: "mounted",
            value: function() {
                this.update_voting();
            }
        }, {
            key: "question",
            get: function() {
                return this.voting && this.voting.questions[this.current_question_index] || {};
            }
        } ]), VoteMainView;
    }(__WEBPACK_IMPORTED_MODULE_0_vue___default.a)) || _class;
}, , , , , , , , , function(module, exports, __webpack_require__) {
    "use strict";
    function createDecorator(factory) {
        return function(target, key, index) {
            var Ctor = target.constructor;
            Ctor.__decorators__ || (Ctor.__decorators__ = []), "number" != typeof index && (index = void 0), 
            Ctor.__decorators__.push(function(options) {
                return factory(options, key, index);
            });
        };
    }
    function collectDataFromConstructor(vm, Component) {
        Component.prototype._init = function() {
            var _this = this, keys = Object.getOwnPropertyNames(vm);
            if (vm.$options.props) for (var key in vm.$options.props) vm.hasOwnProperty(key) || keys.push(key);
            keys.forEach(function(key) {
                "_" !== key.charAt(0) && Object.defineProperty(_this, key, {
                    get: function() {
                        return vm[key];
                    },
                    set: function(value) {
                        return vm[key] = value;
                    }
                });
            });
        };
        var data = new Component(), plainData = {};
        return Object.keys(data).forEach(function(key) {
            void 0 !== data[key] && (plainData[key] = data[key]);
        }), plainData;
    }
    function componentFactory(Component, options) {
        void 0 === options && (options = {}), options.name = options.name || Component._componentTag || Component.name;
        var proto = Component.prototype;
        Object.getOwnPropertyNames(proto).forEach(function(key) {
            if ("constructor" !== key) {
                if ($internalHooks.indexOf(key) > -1) return void (options[key] = proto[key]);
                var descriptor = Object.getOwnPropertyDescriptor(proto, key);
                "function" == typeof descriptor.value ? (options.methods || (options.methods = {}))[key] = descriptor.value : (descriptor.get || descriptor.set) && ((options.computed || (options.computed = {}))[key] = {
                    get: descriptor.get,
                    set: descriptor.set
                });
            }
        }), (options.mixins || (options.mixins = [])).push({
            data: function() {
                return collectDataFromConstructor(this, Component);
            }
        });
        var decorators = Component.__decorators__;
        decorators && decorators.forEach(function(fn) {
            return fn(options);
        });
        var superProto = Object.getPrototypeOf(Component.prototype);
        return (superProto instanceof Vue ? superProto.constructor : Vue).extend(options);
    }
    function Component(options) {
        return "function" == typeof options ? componentFactory(options) : function(Component) {
            return componentFactory(Component, options);
        };
    }
    Object.defineProperty(exports, "__esModule", {
        value: !0
    });
    var Vue = function(ex) {
        return ex && "object" == typeof ex && "default" in ex ? ex.default : ex;
    }(__webpack_require__(1)), $internalHooks = [ "data", "beforeCreate", "created", "beforeMount", "mounted", "beforeDestroy", "destroyed", "beforeUpdate", "updated", "activated", "deactivated", "render" ];
    !function(Component) {
        function registerHooks(keys) {
            $internalHooks.push.apply($internalHooks, keys);
        }
        Component.registerHooks = registerHooks;
    }(Component || (Component = {}));
    var Component$1 = Component;
    exports.default = Component$1, exports.createDecorator = createDecorator;
}, function(module, exports, __webpack_require__) {
    "use strict";
    var Vue = __webpack_require__(1);
    Vue = "default" in Vue ? Vue.default : Vue;
    /^2\./.test(Vue.version) || Vue.util.warn("VueFocus 2.1.0 only supports Vue 2.x, and does not support Vue " + Vue.version);
    var focus = {
        inserted: function(el, binding) {
            binding.value ? el.focus() : el.blur();
        },
        componentUpdated: function(el, binding) {
            binding.modifiers.lazy && Boolean(binding.value) === Boolean(binding.oldValue) || (binding.value ? el.focus() : el.blur());
        }
    }, mixin = {
        directives: {
            focus: focus
        }
    };
    exports.version = "2.1.0", exports.focus = focus, exports.mixin = mixin;
}, , function(module, exports, __webpack_require__) {
    module.exports = __webpack_require__(11);
} ]);
//# sourceMappingURL=voting-vote.entry.js.map