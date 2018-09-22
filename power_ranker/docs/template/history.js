$(document).ready(function () {
		// Loop over all tables on the page
		var tables = document.getElementsByTagName("table");
		for (var i = 0; i < tables.length; i++){
			var table = tables[i];
			var nrows = table.rows.length;
			// Only want to select tables with id that start with "history_table"
			var hist_label = "history_table";
			if (table.id.indexOf(hist_label) <= -1){
				continue;
			}
			console.log(table.id);

			// Insert icons into table
			$('#'+table.id+' tr:eq(1) td:eq(0)').html('<i class="fa fa-trophy" style="color: #f1c40f"></i>');
			$('#'+table.id+' tr:eq(2) td:eq(0)').html('<i class="fa fa-trophy" style="color: #95a5a6"></i>');
			$('#'+table.id+' tr:eq(3) td:eq(0)').html('<i class="fa fa-trophy" style="color: #965A38"></i>');
			$('#'+table.id+' tr:eq('+ (nrows-1) +') td:eq(0)').html('&#128701;');
			
			// Insert table row colors
			$('#'+table.id+' tr:eq(1) td').addClass('row-first');
			$('#'+table.id+' tr:eq(2) td').addClass('row-second');
			$('#'+table.id+' tr:eq(3) td').addClass('row-third');
			$('#'+table.id+' tr:eq('+ (nrows-1) +') td').addClass('row-last');

			// Add Formatting
			$('#'+table.id).DataTable({
				"searching": false,
				"paging": false,
			  "info": false,
				columnDefs: [
					{ targets:[0], orderable:false },
				]	
			}); // end DataTables declaration
		} // end for loop over tables

		// Function to display tables based on drop down selection 
		$(function() {
  		$('#seasonselector').change(function(){
    		$('.season').hide();
    		$('#' + $(this).val()).show();
  		});
	  });

		// Aggregate Season Stats table should have sorting
		$('#aggregate_regular_season').DataTable({
			"searching": false,
			"paging": false,
			"info": false,
			"order":[[3,"desc"]]
		});

		// Aggregate Medal count
		$('#medal_count').DataTable({
			"searching": false,
			"paging": false,
			"info": false,
			"order":[[5,"desc"],[1,"desc"],[2,"desc"],[3,"desc"],[4,"asc"]]
		});
		// Tooltip
		jQuery('[data-toggle="tooltip"]').each(function(){
        var $elem = jQuery($(this));
        $elem.tooltip({
            html:true,
            container: 'body',
            delay: {hide:400}
    		});
		});
});

