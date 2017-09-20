$(document).ready(function () {
    $('#power_table').DataTable(
			    { "paging": false,
				    "info"  : false,						
					  columnDefs : [
					     { targets:[9],orderData:[9,0]}
				     ],
						 "fnRowCallback": function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
								     if( aData[9] == "1"){$('td', nRow).addClass('row-tier1'); } 
								else if( aData[9] == "2"){$('td', nRow).addClass('row-tier2'); } 
								else if( aData[9] == "3"){$('td', nRow).addClass('row-tier3'); } 
								else if( aData[9] == "4"){$('td', nRow).addClass('row-tier4'); } 
								else if( aData[9] == "5"){$('td', nRow).addClass('row-tier5'); } 
						}
		    	}
		);
});

