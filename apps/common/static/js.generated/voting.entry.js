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
    }, __webpack_require__.p = "", __webpack_require__(__webpack_require__.s = 28);
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
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0_deep_equal__ = __webpack_require__(21), __WEBPACK_IMPORTED_MODULE_0_deep_equal___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_deep_equal__), _extends = Object.assign || function(target) {
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i];
            for (var key in source) Object.prototype.hasOwnProperty.call(source, key) && (target[key] = source[key]);
        }
        return target;
    };
    __webpack_exports__.a = {
        props: {
            value: {
                default: ""
            },
            settings: {
                type: Object,
                default: function() {
                    return {};
                }
            }
        },
        data: function() {
            return {
                current: null
            };
        },
        mounted: function() {
            var _this = this;
            $(this.$el).selectize(_extends({
                onInitialize: function() {
                    _this.setValue();
                },
                onChange: function(value) {
                    _this.$emit("input", value);
                }
            }, this.settings));
        },
        computed: {
            options: function() {
                return this.itemOptions ? this.itemOptions : null !== this.current ? this.current.map(function(option) {
                    return {
                        text: option.text,
                        value: option.value
                    };
                }) : void 0;
            }
        },
        watch: {
            value: function() {
                this.setValue();
            },
            options: function(value, old) {
                this.$el.selectize && !__WEBPACK_IMPORTED_MODULE_0_deep_equal___default()(value, old) && (this.$el.selectize.clearOptions(), 
                this.$el.selectize.addOption(this.current), this.$el.selectize.refreshOptions(!1), 
                this.setValue());
            }
        },
        methods: {
            track: function(nodes) {
                this.current = nodes ? nodes.filter(function(node) {
                    return node.tag && "option" === node.tag.toLowerCase();
                }).map(function(node) {
                    return {
                        text: node.children ? node.children[0].text.trim() : null,
                        value: node.data.domProps ? node.data.domProps.value : node.data.attrs.value
                    };
                }) : [];
            },
            setValue: function() {
                __WEBPACK_IMPORTED_MODULE_0_deep_equal___default()(this.$el.selectize.getValue(), this.value) || this.$el.selectize.setValue(this.value);
            }
        },
        render: function(c) {
            return void 0 === this.settings.options && this.track(this.$slots.default), c("select", this.$slots.default);
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1__common_directives_popover__ = __webpack_require__(14);
    __webpack_exports__.a = {
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#question-answer-result-template"),
        props: {
            result: {},
            is_anonymous: Boolean
        },
        directives: {
            popover: __WEBPACK_IMPORTED_MODULE_1__common_directives_popover__.a
        },
        computed: {
            voter_content: function() {
                var content = this.result.voters.map(function(voter) {
                    var vote = "";
                    return voter.first_name && (vote += voter.first_name), voter.last_name && (vote && (vote += " "), 
                    vote += voter.last_name), voter.vote_note && (vote && (vote += ": "), vote += voter.vote_note), 
                    vote;
                }).join("<br/>");
                return this.is_anonymous && (content = content ? __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.anonymous_voting + ":<br/>" + content : __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.anonymous_voting), 
                content;
            }
        },
        methods: {
            max: function(a, b) {
                return Math.max(a, b);
            }
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_2_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_2_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_vue__), __WEBPACK_IMPORTED_MODULE_3__common_components_Vue2Selectize__ = __webpack_require__(7);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)(".voter-form-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        props: [ "voter", "memberships", "existing_voters", "committees" ],
        data: function() {
            return {};
        },
        components: {
            Errors: __WEBPACK_IMPORTED_MODULE_1__common_components_Errors__.a,
            Vue2Selectize: __WEBPACK_IMPORTED_MODULE_3__common_components_Vue2Selectize__.a
        },
        computed: {
            errors: function() {
                return this.voter._errors || __WEBPACK_IMPORTED_MODULE_2_vue___default.a.set(this.voter, "_errors", {}), 
                this.voter._errors;
            },
            available_memberships: function() {
                var selected = {};
                return this.existing_voters.forEach(function(v) {
                    return selected[v.membership] = 1;
                }), this.memberships.filter(function(m) {
                    return !selected[m.id];
                });
            },
            voter_options: function() {
                return this.available_memberships.map(function(m) {
                    return {
                        text: m.first_name + " " + m.last_name,
                        value: {
                            id: m.id
                        }
                    };
                });
            }
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#voters-list-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        props: {
            can_edit: Boolean,
            voters: Array,
            delete: Function
        }
    };
}, , function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    Object.defineProperty(__webpack_exports__, "__esModule", {
        value: !0
    });
    var __WEBPACK_IMPORTED_MODULE_0_vue_router__ = __webpack_require__(5), __WEBPACK_IMPORTED_MODULE_0_vue_router___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_0_vue_router__), __WEBPACK_IMPORTED_MODULE_1_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_1_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vue__), __WEBPACK_IMPORTED_MODULE_2__voting_views_VotingMainView__ = __webpack_require__(18), __WEBPACK_IMPORTED_MODULE_3__voting_views_VotingCreateView__ = __webpack_require__(17), __WEBPACK_IMPORTED_MODULE_4__voting_views_VotingQuestionsView__ = __webpack_require__(19), __WEBPACK_IMPORTED_MODULE_5__common_filters__ = __webpack_require__(4), __WEBPACK_IMPORTED_MODULE_6__voting_views_VotingViewView__ = __webpack_require__(20), admin_routes = [ {
        path: "/",
        component: __WEBPACK_IMPORTED_MODULE_2__voting_views_VotingMainView__.a,
        props: {
            all: !1
        }
    }, {
        path: "/all",
        component: __WEBPACK_IMPORTED_MODULE_2__voting_views_VotingMainView__.a,
        props: {
            all: !0
        }
    }, {
        path: "/create",
        component: __WEBPACK_IMPORTED_MODULE_3__voting_views_VotingCreateView__.a
    }, {
        path: "/view/:id",
        component: __WEBPACK_IMPORTED_MODULE_6__voting_views_VotingViewView__.a
    }, {
        path: "/edit/:id",
        component: __WEBPACK_IMPORTED_MODULE_3__voting_views_VotingCreateView__.a
    }, {
        path: "/questions/:id",
        component: __WEBPACK_IMPORTED_MODULE_4__voting_views_VotingQuestionsView__.a
    }, {
        path: "/*",
        redirect: "/"
    } ], user_routes = [ {
        path: "/",
        component: __WEBPACK_IMPORTED_MODULE_2__voting_views_VotingMainView__.a,
        props: {
            all: !1
        }
    }, {
        path: "/view/:id",
        component: __WEBPACK_IMPORTED_MODULE_6__voting_views_VotingViewView__.a
    }, {
        path: "/*",
        redirect: "/"
    } ], router = new __WEBPACK_IMPORTED_MODULE_0_vue_router___default.a({
        routes: window.is_admin ? admin_routes : user_routes
    });
    __WEBPACK_IMPORTED_MODULE_1_vue___default.a.filter("datetime", __WEBPACK_IMPORTED_MODULE_5__common_filters__.b), 
    __WEBPACK_IMPORTED_MODULE_1_vue___default.a.filter("nl2br", __WEBPACK_IMPORTED_MODULE_5__common_filters__.a), 
    new __WEBPACK_IMPORTED_MODULE_1_vue___default.a({
        router: router
    }).$mount("#app");
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    function parse_date(value) {
        return "string" == typeof value && (value = moment(value).toDate()), value;
    }
    __webpack_exports__.a = {
        inserted: function(el, binding, vnode) {
            var context = vnode.context, keys = binding.expression.split(".");
            $(el).kendoDateTimePicker({
                format: "MMM. dd, yyyy h:mm tt",
                change: function() {
                    var target = context;
                    keys.slice(0, -1).forEach(function(key) {
                        target = target[key];
                    }), target[keys[keys.length - 1]] = this.value();
                }
            });
            var picker = $(el).data("kendoDateTimePicker");
            picker.value(parse_date(binding.value)), picker.trigger("change");
        },
        update: function(el, binding) {
            var picker = $(el).data("kendoDateTimePicker");
            picker.value(parse_date(binding.value)), picker.trigger("change");
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    __webpack_exports__.a = {
        inserted: function(el, binding, vnode) {
            console.log("hey there"), $(el).popover({
                html: !0
            });
        }
    };
}, , function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_2__common_components_Vue2Selectize__ = __webpack_require__(7), __WEBPACK_IMPORTED_MODULE_3_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_3_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_3_vue__);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)(".question-form-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        props: [ "question", "memberships" ],
        data: function() {
            return {
                new_answer: "",
                new_candidate: 0
            };
        },
        components: {
            Errors: __WEBPACK_IMPORTED_MODULE_1__common_components_Errors__.a,
            Vue2Selectize: __WEBPACK_IMPORTED_MODULE_2__common_components_Vue2Selectize__.a
        },
        methods: {
            check_add_answer: function() {
                this.new_answer && (this.question.answers.push({
                    answer: this.new_answer
                }), this.new_answer = "");
            },
            answer_error: function(index) {
                return this.errors.answers && this.errors.answers[index] && this.errors.answers[index].answer;
            }
        },
        watch: {
            new_candidate: function() {
                var _this = this;
                if (this.new_candidate) {
                    var m = this.membership_by_id[this.new_candidate], candidate = {
                        membership: this.new_candidate,
                        first_name: m.first_name,
                        last_name: m.last_name,
                        bio: m.bio,
                        notes: ""
                    };
                    this.question.candidates.push(candidate), __WEBPACK_IMPORTED_MODULE_3_vue___default.a.nextTick(function() {
                        return _this.new_candidate = 0;
                    });
                }
            }
        },
        computed: {
            errors: function() {
                return this.question._errors || __WEBPACK_IMPORTED_MODULE_3_vue___default.a.set(this.question, "_errors", {}), 
                this.question._errors;
            },
            membership_by_id: function() {
                var result = {};
                return this.memberships.forEach(function(m) {
                    return result[m.id] = m;
                }), result;
            },
            available_memberships: function() {
                var selected = {};
                return this.question.candidates.forEach(function(c) {
                    return selected[c.membership] = 1;
                }), this.memberships.filter(function(m) {
                    return !selected[m.id];
                });
            }
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1__components_VoterForm__ = __webpack_require__(9), __WEBPACK_IMPORTED_MODULE_2__components_VotersList__ = __webpack_require__(10), __WEBPACK_IMPORTED_MODULE_3__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_4__common_directives_datetimepicker__ = __webpack_require__(13), __WEBPACK_IMPORTED_MODULE_5__common__ = __webpack_require__(3);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#voting-create-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        data: function() {
            return {
                voting: null,
                memberships: [],
                committees: []
            };
        },
        directives: {
            datetimepicker: __WEBPACK_IMPORTED_MODULE_4__common_directives_datetimepicker__.a
        },
        components: {
            VoterForm: __WEBPACK_IMPORTED_MODULE_1__components_VoterForm__.a,
            VotersList: __WEBPACK_IMPORTED_MODULE_2__components_VotersList__.a,
            Errors: __WEBPACK_IMPORTED_MODULE_3__common_components_Errors__.a
        },
        methods: {
            save: function() {
                var _this = this;
                this._save(function(success, is_new) {
                    is_new ? _this.$router.push("/questions/" + success.id) : _this.$router.push("/view/" + success.id);
                });
            },
            publish: function() {
                var _this2 = this;
                this._save(function(voting) {
                    __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_5__common__.c.make_voting_url(voting.id) + "publish/", "POST").then(function(success) {
                        return _this2.$router.push("/view/" + success.id);
                    }, function(error) {
                        400 === error.status ? Vue.set(_this2.voting, "_errors", error.responseJSON) : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.e)(error);
                    });
                });
            },
            _save: function(on_success) {
                var _this3 = this, is_new = !this.voting.id, copy = __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.f)(this.voting);
                delete copy._errors, copy.add_voters.memberships || copy.add_voters.committees || copy.add_voters.all_members ? (copy.add_voters.memberships = copy.add_voters.memberships || [], 
                copy.add_voters.committees = copy.add_voters.committees || [], copy.add_voters.all_members = copy.add_voters.all_members || []) : delete copy.add_voters;
                var url = is_new ? __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_list : __WEBPACK_IMPORTED_MODULE_5__common__.c.make_voting_url(this.voting.id);
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(url, is_new ? "POST" : "PUT", copy).then(function(success) {
                    on_success(success, is_new);
                }, function(error) {
                    400 === error.status ? _this3.voting._errors = error.responseJSON : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.e)(error);
                });
            },
            init_members: function() {
                var _this4 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_0__common_utils__.d.profiles_memberships_list).then(function(memberships) {
                    return _this4.memberships = memberships.results;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            init_committees: function() {
                var _this5 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_0__common_utils__.d.committees_list).then(function(committees) {
                    return _this5.committees = committees.results;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            init_new_voting: function() {
                this.voting = {
                    name: "",
                    start_time: new Date(),
                    end_time: "",
                    is_anonymous: !1,
                    state: 0,
                    voters: [],
                    add_voters: {
                        all_members: [ "members" ],
                        memberships: [],
                        committees: [],
                        weight: 1
                    }
                };
            },
            init_voting: function() {
                var _this6 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_5__common__.c.make_voting_url(this.$route.params.id)).then(function(data) {
                    _this6.voting = data, _this6.voting.add_voters = {
                        all_members: [],
                        memberships: [],
                        committees: [],
                        weight: 1
                    };
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            delete_voter: function(voter) {
                var _this7 = this;
                swal({
                    title: trans.delete_voter,
                    text: trans.delete_voter_text,
                    type: "warning",
                    showCancelButton: !0,
                    confirmButtonClass: "bg-danger",
                    confirmButtonText: trans.delete_text,
                    cancelButtonText: trans.cancel_text
                }).then(function() {
                    __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_5__common__.c.make_voter_url(voter), "DELETE").then(function(success) {
                        return _this7.init_voting();
                    }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
                }, function() {});
            }
        },
        computed: {
            errors: function() {
                return this.voting._errors || Vue.set(this.voting, "_errors", {}), this.voting._errors;
            }
        },
        mounted: function() {
            $("#content").addClass("has-right-side"), this.init_members(), this.init_committees(), 
            this.$route.params.id ? this.init_voting() : this.init_new_voting();
        },
        destroyed: function() {
            $("#content").removeClass("has-right-side");
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1_vuejs_paginate__ = __webpack_require__(26), __WEBPACK_IMPORTED_MODULE_1_vuejs_paginate___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vuejs_paginate__);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#main-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        props: [ "all" ],
        components: {
            paginate: __WEBPACK_IMPORTED_MODULE_1_vuejs_paginate___default.a
        },
        data: function() {
            return {
                votings: [],
                is_admin: window.is_admin,
                page_size: 50,
                page: 1
            };
        },
        methods: {
            update_voting_list: function() {
                var that = this, url = this.is_admin && this.all ? __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_list : __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.available_votings_list;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(url + "?page=" + this.page).then(function(data) {
                    that.votings = data;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            show_page: function(page) {
                this.page = page, this.update_voting_list();
            }
        },
        watch: {
            all: function() {
                this.update_voting_list();
            }
        },
        beforeRouteUpdate: function() {
            console.log("before update"), this.update_voting_list();
        },
        mounted: function() {
            console.log("mounted"), this.update_voting_list();
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_1_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vue__), __WEBPACK_IMPORTED_MODULE_2__components_QuestionForm__ = __webpack_require__(16), __WEBPACK_IMPORTED_MODULE_3__components_VoterForm__ = __webpack_require__(9), __WEBPACK_IMPORTED_MODULE_4__components_QuestionAnswerResult__ = __webpack_require__(8), __WEBPACK_IMPORTED_MODULE_5__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_6__common__ = __webpack_require__(3);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#voting-questions-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        data: function() {
            return {
                voting: {},
                memberships: [],
                committees: [],
                edit_questions: {}
            };
        },
        components: {
            QuestionForm: __WEBPACK_IMPORTED_MODULE_2__components_QuestionForm__.a,
            VoterForm: __WEBPACK_IMPORTED_MODULE_3__components_VoterForm__.a,
            QuestionAnswerResult: __WEBPACK_IMPORTED_MODULE_4__components_QuestionAnswerResult__.a,
            Errors: __WEBPACK_IMPORTED_MODULE_5__common_components_Errors__.a
        },
        methods: {
            init_voting: function() {
                var _this = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_6__common__.c.make_voting_url(this.$route.params.id)).then(function(data) {
                    _this.voting = data, _this.voting.questions.length || _this.add_question(), _this.voting.voters.length || _this.add_voter();
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            init_members: function() {
                var _this2 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_0__common_utils__.d.profiles_memberships_list).then(function(memberships) {
                    return _this2.memberships = memberships.results;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            init_committees: function() {
                var _this3 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_0__common_utils__.d.committees_list).then(function(committees) {
                    return _this3.committees = committees.results;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            add_question: function() {
                __WEBPACK_IMPORTED_MODULE_1_vue___default.a.set(this.edit_questions, 0, {
                    question_type: 1,
                    question: "",
                    voting: this.voting.id,
                    ordering: 1e3,
                    answers: [],
                    candidates: []
                });
            },
            start_edit_question: function(question) {
                __WEBPACK_IMPORTED_MODULE_1_vue___default.a.set(this.edit_questions, question.id, __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.f)(question));
            },
            save_question: function(question) {
                var _this4 = this, data = __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.f)(question);
                delete data._errors, __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_6__common__.c.make_question_url(question), question.id ? "PUT" : "POST", data).then(function(success) {
                    _this4.init_voting(), _this4.edit_questions[question.id || 0] = null;
                }, function(error) {
                    400 === error.status ? question._errors = error.responseJSON : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.e)(error);
                });
            },
            delete_question: function(question) {
                var _this5 = this;
                swal({
                    title: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_question,
                    text: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_question_text,
                    type: "warning",
                    showCancelButton: !0,
                    confirmButtonClass: "bg-danger",
                    confirmButtonText: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_text,
                    cancelButtonText: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.cancel_text
                }).then(function() {
                    __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_6__common__.c.make_question_url(question), "DELETE").then(function(success) {
                        return _this5.init_voting();
                    }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
                }, function() {});
            },
            publish: function() {
                var _this6 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_6__common__.c.make_voting_url(this.voting.id) + "publish/", "POST").then(function(success) {
                    return _this6.$router.push("/view/" + success.id);
                }, function(error) {
                    400 === error.status ? __WEBPACK_IMPORTED_MODULE_1_vue___default.a.set(_this6.voting, "_errors", error.responseJSON) : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.e)(error);
                });
            },
            answer_result: function(question_id, answer_id) {
                return this.voting.result && this.voting.result.questions[question_id] && this.voting.result.questions[question_id][answer_id];
            }
        },
        computed: {
            membership_by_id: function() {
                var result = {};
                return this.memberships.forEach(function(m) {
                    return result[m.id] = m;
                }), result;
            }
        },
        mounted: function() {
            this.init_voting(), this.init_members(), this.init_committees(), $("#content").addClass("has-right-side");
        },
        destroyed: function() {
            $("#content").removeClass("has-right-side");
        }
    };
}, function(module, __webpack_exports__, __webpack_require__) {
    "use strict";
    var __WEBPACK_IMPORTED_MODULE_0__common_utils__ = __webpack_require__(0), __WEBPACK_IMPORTED_MODULE_1_vue__ = __webpack_require__(1), __WEBPACK_IMPORTED_MODULE_1_vue___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_1_vue__), __WEBPACK_IMPORTED_MODULE_2__components_QuestionAnswerResult__ = __webpack_require__(8), __WEBPACK_IMPORTED_MODULE_3__common_components_Errors__ = __webpack_require__(2), __WEBPACK_IMPORTED_MODULE_4__components_VotersList__ = __webpack_require__(10), __WEBPACK_IMPORTED_MODULE_5__common__ = __webpack_require__(3);
    __webpack_exports__.a = {
        template: __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.a)("#voting-view-template"),
        delimiters: __WEBPACK_IMPORTED_MODULE_0__common_utils__.b,
        data: function() {
            return {
                voting: {},
                quorum_is_met: !1,
                is_admin: __WEBPACK_IMPORTED_MODULE_0__common_utils__.h
            };
        },
        components: {
            QuestionAnswerResult: __WEBPACK_IMPORTED_MODULE_2__components_QuestionAnswerResult__.a,
            VotersList: __WEBPACK_IMPORTED_MODULE_4__components_VotersList__.a,
            Errors: __WEBPACK_IMPORTED_MODULE_3__common_components_Errors__.a
        },
        methods: {
            init_voting: function() {
                var _this = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(this.make_voting_url(this.$route.params.id)).then(function(voting) {
                    return _this.voting = voting;
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            publish: function() {
                var _this2 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(this.make_voting_url(this.voting.id) + "publish/", "POST").then(function(success) {
                    return _this2.init_voting();
                }, function(error) {
                    400 === error.status ? __WEBPACK_IMPORTED_MODULE_1_vue___default.a.set(_this2.voting, "_errors", error.responseJSON) : __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.e)(error);
                });
            },
            publish_results: function() {
                var _this3 = this;
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(this.make_voting_url(this.voting.id) + "publish_results/", "POST").then(function(success) {
                    return _this3.init_voting();
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            resend_email: function() {
                __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(this.make_voting_url(this.voting.id) + "publish/", "POST").then(function(success) {
                    swal({
                        title: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.success,
                        text: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.resend_done,
                        type: "success"
                    });
                }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
            },
            make_voting_url: function(voting_id) {
                return __WEBPACK_IMPORTED_MODULE_0__common_utils__.d.votings_detail.replace("9999", voting_id);
            },
            answer_result: function(question_id, answer_id) {
                return this.voting.result && this.voting.result.questions[question_id] && this.voting.result.questions[question_id][answer_id];
            },
            delete_voting: function() {
                var _this4 = this;
                swal({
                    title: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_voting,
                    text: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_voting_text,
                    type: "warning",
                    showCancelButton: !0,
                    confirmButtonClass: "bg-danger",
                    confirmButtonText: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.delete_text,
                    cancelButtonText: __WEBPACK_IMPORTED_MODULE_0__common_utils__.g.cancel_text
                }).then(function() {
                    __webpack_require__.i(__WEBPACK_IMPORTED_MODULE_0__common_utils__.c)(__WEBPACK_IMPORTED_MODULE_5__common__.c.make_voting_url(_this4.voting.id), "DELETE").then(function(success) {
                        return _this4.$router.push("/");
                    }, __WEBPACK_IMPORTED_MODULE_0__common_utils__.e);
                }, function() {});
            }
        },
        mounted: function() {
            this.init_voting(), $("#content").addClass("has-right-side");
        },
        destroyed: function() {
            $("#content").removeClass("has-right-side");
        }
    };
}, function(module, exports, __webpack_require__) {
    function isUndefinedOrNull(value) {
        return null === value || void 0 === value;
    }
    function isBuffer(x) {
        return !(!x || "object" != typeof x || "number" != typeof x.length) && ("function" == typeof x.copy && "function" == typeof x.slice && !(x.length > 0 && "number" != typeof x[0]));
    }
    function objEquiv(a, b, opts) {
        var i, key;
        if (isUndefinedOrNull(a) || isUndefinedOrNull(b)) return !1;
        if (a.prototype !== b.prototype) return !1;
        if (isArguments(a)) return !!isArguments(b) && (a = pSlice.call(a), b = pSlice.call(b), 
        deepEqual(a, b, opts));
        if (isBuffer(a)) {
            if (!isBuffer(b)) return !1;
            if (a.length !== b.length) return !1;
            for (i = 0; i < a.length; i++) if (a[i] !== b[i]) return !1;
            return !0;
        }
        try {
            var ka = objectKeys(a), kb = objectKeys(b);
        } catch (e) {
            return !1;
        }
        if (ka.length != kb.length) return !1;
        for (ka.sort(), kb.sort(), i = ka.length - 1; i >= 0; i--) if (ka[i] != kb[i]) return !1;
        for (i = ka.length - 1; i >= 0; i--) if (key = ka[i], !deepEqual(a[key], b[key], opts)) return !1;
        return typeof a == typeof b;
    }
    var pSlice = Array.prototype.slice, objectKeys = __webpack_require__(23), isArguments = __webpack_require__(22), deepEqual = module.exports = function(actual, expected, opts) {
        return opts || (opts = {}), actual === expected || (actual instanceof Date && expected instanceof Date ? actual.getTime() === expected.getTime() : !actual || !expected || "object" != typeof actual && "object" != typeof expected ? opts.strict ? actual === expected : actual == expected : objEquiv(actual, expected, opts));
    };
}, function(module, exports) {
    function supported(object) {
        return "[object Arguments]" == Object.prototype.toString.call(object);
    }
    function unsupported(object) {
        return object && "object" == typeof object && "number" == typeof object.length && Object.prototype.hasOwnProperty.call(object, "callee") && !Object.prototype.propertyIsEnumerable.call(object, "callee") || !1;
    }
    var supportsArgumentsClass = "[object Arguments]" == function() {
        return Object.prototype.toString.call(arguments);
    }();
    exports = module.exports = supportsArgumentsClass ? supported : unsupported, exports.supported = supported, 
    exports.unsupported = unsupported;
}, function(module, exports) {
    function shim(obj) {
        var keys = [];
        for (var key in obj) keys.push(key);
        return keys;
    }
    exports = module.exports = "function" == typeof Object.keys ? Object.keys : shim, 
    exports.shim = shim;
}, , , function(module, exports, __webpack_require__) {
    !function(e, t) {
        module.exports = t();
    }(0, function() {
        return function(e) {
            function t(s) {
                if (n[s]) return n[s].exports;
                var i = n[s] = {
                    exports: {},
                    id: s,
                    loaded: !1
                };
                return e[s].call(i.exports, i, i.exports, t), i.loaded = !0, i.exports;
            }
            var n = {};
            return t.m = e, t.c = n, t.p = "", t(0);
        }([ function(e, t, n) {
            "use strict";
            var i = n(1), r = function(e) {
                return e && e.__esModule ? e : {
                    default: e
                };
            }(i);
            e.exports = r.default;
        }, function(e, t, n) {
            n(2);
            var s = n(6)(n(7), n(8), "data-v-82963a40", null);
            e.exports = s.exports;
        }, function(e, t, n) {
            var s = n(3);
            "string" == typeof s && (s = [ [ e.id, s, "" ] ]), n(5)(s, {}), s.locals && (e.exports = s.locals);
        }, function(e, t, n) {
            t = e.exports = n(4)(), t.push([ e.id, "a[data-v-82963a40]{cursor:pointer}", "" ]);
        }, function(e, t) {
            e.exports = function() {
                var e = [];
                return e.toString = function() {
                    for (var e = [], t = 0; t < this.length; t++) {
                        var n = this[t];
                        n[2] ? e.push("@media " + n[2] + "{" + n[1] + "}") : e.push(n[1]);
                    }
                    return e.join("");
                }, e.i = function(t, n) {
                    "string" == typeof t && (t = [ [ null, t, "" ] ]);
                    for (var s = {}, i = 0; i < this.length; i++) {
                        var r = this[i][0];
                        "number" == typeof r && (s[r] = !0);
                    }
                    for (i = 0; i < t.length; i++) {
                        var a = t[i];
                        "number" == typeof a[0] && s[a[0]] || (n && !a[2] ? a[2] = n : n && (a[2] = "(" + a[2] + ") and (" + n + ")"), 
                        e.push(a));
                    }
                }, e;
            };
        }, function(e, t, n) {
            function s(e, t) {
                for (var n = 0; n < e.length; n++) {
                    var s = e[n], i = d[s.id];
                    if (i) {
                        i.refs++;
                        for (var r = 0; r < i.parts.length; r++) i.parts[r](s.parts[r]);
                        for (;r < s.parts.length; r++) i.parts.push(c(s.parts[r], t));
                    } else {
                        for (var a = [], r = 0; r < s.parts.length; r++) a.push(c(s.parts[r], t));
                        d[s.id] = {
                            id: s.id,
                            refs: 1,
                            parts: a
                        };
                    }
                }
            }
            function i(e) {
                for (var t = [], n = {}, s = 0; s < e.length; s++) {
                    var i = e[s], r = i[0], a = i[1], o = i[2], c = i[3], l = {
                        css: a,
                        media: o,
                        sourceMap: c
                    };
                    n[r] ? n[r].parts.push(l) : t.push(n[r] = {
                        id: r,
                        parts: [ l ]
                    });
                }
                return t;
            }
            function r(e, t) {
                var n = h(), s = x[x.length - 1];
                if ("top" === e.insertAt) s ? s.nextSibling ? n.insertBefore(t, s.nextSibling) : n.appendChild(t) : n.insertBefore(t, n.firstChild), 
                x.push(t); else {
                    if ("bottom" !== e.insertAt) throw new Error("Invalid value for parameter 'insertAt'. Must be 'top' or 'bottom'.");
                    n.appendChild(t);
                }
            }
            function a(e) {
                e.parentNode.removeChild(e);
                var t = x.indexOf(e);
                t >= 0 && x.splice(t, 1);
            }
            function o(e) {
                var t = document.createElement("style");
                return t.type = "text/css", r(e, t), t;
            }
            function c(e, t) {
                var n, s, i;
                if (t.singleton) {
                    var r = v++;
                    n = g || (g = o(t)), s = l.bind(null, n, r, !1), i = l.bind(null, n, r, !0);
                } else n = o(t), s = u.bind(null, n), i = function() {
                    a(n);
                };
                return s(e), function(t) {
                    if (t) {
                        if (t.css === e.css && t.media === e.media && t.sourceMap === e.sourceMap) return;
                        s(e = t);
                    } else i();
                };
            }
            function l(e, t, n, s) {
                var i = n ? "" : s.css;
                if (e.styleSheet) e.styleSheet.cssText = m(t, i); else {
                    var r = document.createTextNode(i), a = e.childNodes;
                    a[t] && e.removeChild(a[t]), a.length ? e.insertBefore(r, a[t]) : e.appendChild(r);
                }
            }
            function u(e, t) {
                var n = t.css, s = t.media, i = t.sourceMap;
                if (s && e.setAttribute("media", s), i && (n += "\n/*# sourceURL=" + i.sources[0] + " */", 
                n += "\n/*# sourceMappingURL=data:application/json;base64," + btoa(unescape(encodeURIComponent(JSON.stringify(i)))) + " */"), 
                e.styleSheet) e.styleSheet.cssText = n; else {
                    for (;e.firstChild; ) e.removeChild(e.firstChild);
                    e.appendChild(document.createTextNode(n));
                }
            }
            var d = {}, p = function(e) {
                var t;
                return function() {
                    return void 0 === t && (t = e.apply(this, arguments)), t;
                };
            }, f = p(function() {
                return /msie [6-9]\b/.test(window.navigator.userAgent.toLowerCase());
            }), h = p(function() {
                return document.head || document.getElementsByTagName("head")[0];
            }), g = null, v = 0, x = [];
            e.exports = function(e, t) {
                t = t || {}, void 0 === t.singleton && (t.singleton = f()), void 0 === t.insertAt && (t.insertAt = "bottom");
                var n = i(e);
                return s(n, t), function(e) {
                    for (var r = [], a = 0; a < n.length; a++) {
                        var o = n[a], c = d[o.id];
                        c.refs--, r.push(c);
                    }
                    if (e) {
                        s(i(e), t);
                    }
                    for (var a = 0; a < r.length; a++) {
                        var c = r[a];
                        if (0 === c.refs) {
                            for (var u = 0; u < c.parts.length; u++) c.parts[u]();
                            delete d[c.id];
                        }
                    }
                };
            };
            var m = function() {
                var e = [];
                return function(t, n) {
                    return e[t] = n, e.filter(Boolean).join("\n");
                };
            }();
        }, function(e, t) {
            e.exports = function(e, t, n, s) {
                var i, r = e = e || {}, a = typeof e.default;
                "object" !== a && "function" !== a || (i = e, r = e.default);
                var o = "function" == typeof r ? r.options : r;
                if (t && (o.render = t.render, o.staticRenderFns = t.staticRenderFns), n && (o._scopeId = n), 
                s) {
                    var c = o.computed || (o.computed = {});
                    Object.keys(s).forEach(function(e) {
                        var t = s[e];
                        c[e] = function() {
                            return t;
                        };
                    });
                }
                return {
                    esModule: i,
                    exports: r,
                    options: o
                };
            };
        }, function(e, t) {
            "use strict";
            Object.defineProperty(t, "__esModule", {
                value: !0
            }), t.default = {
                props: {
                    pageCount: {
                        type: Number,
                        required: !0
                    },
                    initialPage: {
                        type: Number,
                        default: 0
                    },
                    forcePage: {
                        type: Number
                    },
                    clickHandler: {
                        type: Function,
                        default: function() {}
                    },
                    pageRange: {
                        type: Number,
                        default: 3
                    },
                    marginPages: {
                        type: Number,
                        default: 1
                    },
                    prevText: {
                        type: String,
                        default: "Prev"
                    },
                    nextText: {
                        type: String,
                        default: "Next"
                    },
                    containerClass: {
                        type: String
                    },
                    pageClass: {
                        type: String
                    },
                    pageLinkClass: {
                        type: String
                    },
                    prevClass: {
                        type: String
                    },
                    prevLinkClass: {
                        type: String
                    },
                    nextClass: {
                        type: String
                    },
                    nextLinkClass: {
                        type: String
                    }
                },
                data: function() {
                    return {
                        selected: this.initialPage
                    };
                },
                beforeUpdate: function() {
                    void 0 !== this.forcePage && this.forcePage !== this.selected && (this.selected = this.forcePage);
                },
                computed: {
                    pages: function() {
                        var e = {};
                        if (this.pageCount <= this.pageRange) for (var t = 0; t < this.pageCount; t++) {
                            var n = {
                                index: t,
                                content: t + 1,
                                selected: t === this.selected
                            };
                            e[t] = n;
                        } else {
                            var s = this.pageRange / 2, i = this.pageRange - s;
                            this.selected < s ? (s = this.selected, i = this.pageRange - s) : this.selected > this.pageCount - this.pageRange / 2 && (i = this.pageCount - this.selected, 
                            s = this.pageRange - i);
                            for (var r = 0; r < this.pageCount; r++) {
                                var a = {
                                    index: r,
                                    content: r + 1,
                                    selected: r === this.selected
                                };
                                if (r <= this.marginPages - 1 || r >= this.pageCount - this.marginPages) e[r] = a; else {
                                    var o = {
                                        content: "...",
                                        disabled: !0
                                    };
                                    this.selected - s > this.marginPages && e[this.marginPages] !== o && (e[this.marginPages] = o), 
                                    this.selected + i < this.pageCount - this.marginPages - 1 && e[this.pageCount - this.marginPages - 1] !== o && (e[this.pageCount - this.marginPages - 1] = o);
                                    var c = this.selected + i - this.pageCount + 1;
                                    c > 0 && r === this.selected - s - c && (e[r] = a), r >= this.selected - s && r <= this.selected + i && (e[r] = a);
                                }
                            }
                        }
                        return e;
                    }
                },
                methods: {
                    handlePageSelected: function(e) {
                        this.selected !== e && (this.selected = e, this.clickHandler(this.selected + 1));
                    },
                    prevPage: function() {
                        this.selected <= 0 || (this.selected--, this.clickHandler(this.selected + 1));
                    },
                    nextPage: function() {
                        this.selected >= this.pageCount - 1 || (this.selected++, this.clickHandler(this.selected + 1));
                    },
                    firstPageSelected: function() {
                        return 0 === this.selected;
                    },
                    lastPageSelected: function() {
                        return this.selected === this.pageCount - 1 || 0 === this.pageCount;
                    }
                }
            };
        }, function(e, t) {
            e.exports = {
                render: function() {
                    var e = this, t = e.$createElement, n = e._self._c || t;
                    return n("ul", {
                        class: e.containerClass
                    }, [ n("li", {
                        class: [ e.prevClass, {
                            disabled: e.firstPageSelected()
                        } ]
                    }, [ n("a", {
                        class: e.prevLinkClass,
                        attrs: {
                            tabindex: "0"
                        },
                        on: {
                            click: function(t) {
                                e.prevPage();
                            },
                            keyup: function(t) {
                                e._k(t.keyCode, "enter", 13) || e.prevPage();
                            }
                        }
                    }, [ e._v(e._s(e.prevText)) ]) ]), e._v(" "), e._l(e.pages, function(t) {
                        return n("li", {
                            class: [ e.pageClass, {
                                active: t.selected,
                                disabled: t.disabled
                            } ]
                        }, [ t.disabled ? n("a", {
                            class: e.pageLinkClass,
                            attrs: {
                                tabindex: "0"
                            }
                        }, [ e._v(e._s(t.content)) ]) : n("a", {
                            class: e.pageLinkClass,
                            attrs: {
                                tabindex: "0"
                            },
                            on: {
                                click: function(n) {
                                    e.handlePageSelected(t.index);
                                },
                                keyup: function(n) {
                                    e._k(n.keyCode, "enter", 13) || e.handlePageSelected(t.index);
                                }
                            }
                        }, [ e._v(e._s(t.content)) ]) ]);
                    }), e._v(" "), n("li", {
                        class: [ e.nextClass, {
                            disabled: e.lastPageSelected()
                        } ]
                    }, [ n("a", {
                        class: e.nextLinkClass,
                        attrs: {
                            tabindex: "0"
                        },
                        on: {
                            click: function(t) {
                                e.nextPage();
                            },
                            keyup: function(t) {
                                e._k(t.keyCode, "enter", 13) || e.nextPage();
                            }
                        }
                    }, [ e._v(e._s(e.nextText)) ]) ]) ], 2);
                },
                staticRenderFns: []
            };
        } ]);
    });
}, , function(module, exports, __webpack_require__) {
    module.exports = __webpack_require__(12);
} ]);
//# sourceMappingURL=voting.entry.js.map