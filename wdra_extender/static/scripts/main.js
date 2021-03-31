function check_long_task(status_url, prog_bar, prog_status, prog_msg) {
        // create a progress bar
        div = $('<div class="progress"></div>');
        $(prog_bar).append(div);
        var nanobar = new Nanobar({
            bg: '#44f',
            target: div[0]
        });
        // check the progress of the task
        update_progress(status_url, nanobar, prog_status, prog_msg, 0);
    }
    function update_progress(status_url, nanobar, prog_status, prog_msg, re_runs) {
        // send GET request to status URL
        rerun_in = 1;
        $.getJSON(status_url, function(data) {
            // update UI
            if (re_runs === undefined) {
                re_runs = 0;
            }
            percent = 0;
            $(prog_status).text(data['state']);
            if (data['state'] === 'PENDING') {
                //update status
                // set nanobar to queue position
                $(prog_msg).text('Waiting in the job queue.');
                //rerun in
                rerun_in = 10*(re_runs+1);
            }
            if (data['state'] === 'STARTING' || data['state'] === 'COLLECTING') {
                //update status
                // set nanobar to be the total number to collect
                percent = parseInt(100 * data['collected'] / data['max_results']);
                $(prog_msg).text('Collecting Tweets');
                //rerun in
                rerun_in = 5 + (re_runs * ((100 - percent) / 100));
            }
            if (data['state'] === 'RATE_LIMITING') {
                //update status
                // set nanobar to be the time to retry
                $(prog_msg).text('Rate Limit hit');
                percent = parseInt(100 * ((Date.now()/1000) - data['sleep_start']) / data['sleep']);
                //rerun in
                rerun_in = data['sleep'] / 10;
            }
            nanobar.go(percent);
        });
        // rerun in `rerun_in` seconds
        setTimeout(function() {
            update_progress(status_url, nanobar, prog_status, prog_msg, re_runs+1);
        }, ~~(rerun_in*1000));
    }