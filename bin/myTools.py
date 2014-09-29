
def mapToPixel(mx,my,gt):
    ''' Convert map to pixel coordinates
        @param  mx    Input map x coordinate (double)
        @param  my    Input map y coordinate (double)
        @param  gt    Input geotransform (six doubles)
        @return px,py Output coordinates (two doubles)
    '''
    if gt[2]+gt[4]==0: #Simple calc, no inversion required
        px = (mx - gt[0]) / gt[1]
        py = (my - gt[3]) / gt[5]
    else:
        px,py = ApplyGeoTransform(mx, my, InvGeoTransform(gt))
    return int(px+0.5),int(py+0.5)

def pixelToMap(px,py,gt):
    ''' Convert pixel to map coordinates
        @param  px    Input pixel x coordinate (double)
        @param  py    Input pixel y coordinate (double)
        @param  gt    Input geotransform (six doubles)
        @return mx,my Output coordinates (two doubles)
    '''
    mx,my=ApplyGeoTransform(px,py,gt)
    return mx,my

def ApplyGeoTransform(inx, iny, gt):
    ''' Apply a geotransform
        @param  inx       Input x coordinate (double)
        @param  iny       Input y coordinate (double)
        @param  gt        Input geotransform (six doubles)
        @return outx,outy Output coordinates (two doubles)
    '''
    outx = gt[0] + inx*gt[1] + iny*gt[2]
    outy = gt[3] + inx*gt[4] + iny*gt[5]
    return (outx,outy)

def InvGeoTransform(gt_in):
    # This function will invert a standard 3x2 set of GeoTransform coefficients.
    # @param  gt_in  Input geotransform (six doubles - unaltered).
    # @return gt_out Output geotransform (six doubles - updated) on success,
    #                None if the equation is uninvertable. 
     
    # we assume a 3rd row that is [1 0 0]

    # Compute determinate
    det = gt_in[1] * gt_in[5] - gt_in[2] * gt_in[4]

    if( abs(det) < 0.000000000000001 ):
        return
    
    inv_det = 1.0 / det

    # compute adjoint, and divide by determinate
    gt_out = [0,0,0,0,0,0]
    gt_out[1] =  gt_in[5] * inv_det
    gt_out[4] = -gt_in[4] * inv_det

    gt_out[2] = -gt_in[2] * inv_det
    gt_out[5] =  gt_in[1] * inv_det

    gt_out[0] = ( gt_in[2] * gt_in[3] - gt_in[0] * gt_in[5]) * inv_det
    gt_out[3] = (-gt_in[1] * gt_in[3] + gt_in[0] * gt_in[4]) * inv_det

    return gt_out

