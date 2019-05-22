import $ from 'jquery';

export const delimiters = ['${', '}'];
export const urls = window.urls;
export const trans = window.trans;
export const is_admin = window.is_admin;

export function template(id) {
    "use strict";
    const element = $(id);
    if (!element.length) {
        throw "Can't find template '" + id + "'.";
    } else if (element.length > 1) {
        throw "More then 1 template '" + id + "' found.";
    }
    return element[0].outerHTML;
}

export function error_handler(response) {
    console.error(response);
    let message;
    if (response.responseJSON && response.responseJSON[0]) {
        message = response.responseJSON[0];
    } else if (response.responseJSON && response.responseJSON.error) {
        message = response.responseJSON.error;
    } else if (response.responseJSON && response.responseJSON.message) {
        message = response.responseJSON.message;
    } else if (response.responseJSON && response.responseJSON.detail) {
        message = response.responseJSON.detail;
    } else if (response.responseJSON && response.responseJSON.non_field_errors) {
        message = response.responseJSON.non_field_errors[0];
    } else {
        message = response.statusText;
    }
    swal(trans.error, message, 'error');
}

/**
 * Very simple wrapper, to still use jquery.ajax (and global cookie setup for it), but not bother with JSON and complex params.
 */
export function request(url, method, data) {
    method = method || 'GET';

    let request = {
        url,
        method,
    };

    if (method === 'POST' || method === 'PATCH' || method === 'PUT') {
        request.data = JSON.stringify(data);
        request.contentType = 'application/json';
    } else if (data) {
        console.error('data is not empty and method is not POST|PATCH|PUT');
    }

    return $.ajax(request);
}

export function deep_copy(object) {
    return $.extend(true, {}, object);
}