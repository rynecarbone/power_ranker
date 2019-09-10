$(document).ready(function () {
    $('#power_table').DataTable(
			    {"paging": false,
				 "info"  : false,
				 "searching": false,
				 columnDefs : [
				    {targets:[12], orderData:[12,0]}
				 ],
				"fnRowCallback": function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
				    if( aData[12] == "1"){$('td', nRow).addClass('row-tier1'); }
					else if( aData[12] == "2"){$('td', nRow).addClass('row-tier2'); }
					else if( aData[12] == "3"){$('td', nRow).addClass('row-tier3'); }
					else if( aData[12] == "4"){$('td', nRow).addClass('row-tier4'); }
					else if( aData[12] == "5"){$('td', nRow).addClass('row-tier5'); }
				    }
		    	}
	);
});

