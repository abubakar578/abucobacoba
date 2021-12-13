odoo.define('fal_activity_meeting/static/src/js/fal_activity_meeting.js', function (require) {
    "use strict";

const components = {
    Activity: require('mail/static/src/components/activity/activity.js'),
};
const { patch } = require('web.utils');

patch(components.Activity, 'fal_activity_meeting/static/src/js/fal_activity_meeting.js', {
    _onCreateMeeting: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        console.log(ev.currentTarget.dataset.activityId)
        console.log(ev)
        var self = this;
        var meeting_id ;
        var kwargs = {}
        self.env.services.rpc({
            model: 'mail.activity',
            method: 'get_meeeting_id',
            args: [{
                'activity_id': this.props.activityLocalId
            }],
            kwargs: kwargs,
        }).then(function (result) {
            const action = {
                name: self.env._t("Meeting"),
                type: 'ir.actions.act_window',
                res_model: 'calendar.event',
                res_id: result,
                views: [[false, 'form']],
                target: 'current',
                context: {'edit': true, 'create': 0},
            };
            self.env.bus.trigger('do-action', {
                action,
            });
        })
        console.log('THIS IS RRRRRRRR')
        console.log(this.props.activityLocalId)
    }
});
});
