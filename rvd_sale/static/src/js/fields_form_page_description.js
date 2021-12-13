odoo.define('rvd_sale.fields_form', function (require) {
"use strict";

var FieldRegistry = require('web.field_registry');
var FieldChar = require('web.basic_fields').FieldChar;

var FormDescriptionPage = FieldChar.extend({
    /**
     * @private
     * @override
     */
    _renderEdit: function () {
        var def = this._super.apply(this, arguments);
        this.$el.addClass('col');
        var $inputGroup = $('<div class="input-group">');
        this.$el = $inputGroup.append(this.$el);
        var $button = $(
            '<div class="input-group-append">\
                <button type="button" title="Open section" class="btn oe_edit_only o_icon_button">\
                    <i class="fa fa-fw o_button_icon fa fa-eye"/>\
                </button>\
            </div>'
        );
        this.$el = this.$el.append($button);
        console.log(this.$el)
        $button.on('click', this._onClickEdit.bind(this));

        return def;
    },
    //--------------------------------------------------------------------------
    // Pop Up Choose Product
    //--------------------------------------------------------------------------
    /**
     * @private
     */
    _onClickEdit: function (ev) {
        ev.stopPropagation();
        var self = this;
        var kwargs = {}
        this._rpc({
            model: 'sale.order.line',
            method: 'get_choose_product',
            args: [self.res_id],
            kwargs: kwargs,
        })
        .then(function (result){
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'choose.product.select',
                res_id: result,
                views: [[false, 'form']],
                target: 'new',
                context: {'edit': false, 'create': 0},
            });
        })    
    },
});

FieldRegistry.add('so_description_page', FormDescriptionPage);

});
