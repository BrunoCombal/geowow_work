# \author Bruno Combal
# \date January 2013
# \brief Create animation files for display in an HTML page

library(animation)

# source http://code.google.com/p/miscell/source/browse/rvalues/rvalues.r
':=' = function(lhs, rhs) {
	frame = parent.frame()
	lhs = as.list(substitute(lhs))
	if (length(lhs) > 1)
		lhs = lhs[-1]
	if (length(lhs) == 1) {
		do.call(`=`, list(lhs[[1]], rhs), envir=frame)
		return(invisible(NULL)) }
	if (is.function(rhs) || is(rhs, 'formula'))
		rhs = list(rhs)
	if (length(lhs) > length(rhs))
		rhs = c(rhs, rep(list(NULL), length(lhs) - length(rhs)))
	for (i in 1:length(lhs))
		do.call(`=`, list(lhs[[i]], rhs[[i]]), envir=frame)
	return(invisible(NULL)) }


incrementDate<-function(year, month){
	month <- month + 1
	if (month>=13) {
		month <- 1
		year = year+1
	}
	return( c(year, month) )
}

inDir<-'/Users/bruno/Desktop/UNESCO/geowow/codes/indicators/outdata/'
inFileBase<-'zos_delta_'
yearStart=2006
monthStart=1
ndate=1139

year <- yearStart
month <- monthStart
for (idate in 1:ndate){
	c(year, month) := incrementDate(year, month)
	fileToDisplay = paste(inDir,"/",inFileBase,"_",year,"_",month,".tif",sep="")
	image(fileToDisplay)
	ani.pause()
}
