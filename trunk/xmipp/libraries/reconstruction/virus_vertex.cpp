/***************************************************************************
 *
 * Authors:     Roberto Marabini (roberto@cnb.uam.es)
 *
 * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307  USA
 *
 *  All comments concerning this program package may be sent to the
 *  e-mail address 'xmipp@cnb.uam.es'
 ***************************************************************************/

#include "virus_vertex.h"



/* Read parameters from command line. -------------------------------------- */
void VirusVertex::read(int argc, char **argv)
{
    fn_sel  = getParameter(argc, argv,  "-sel");
    fn_doc  = getParameter(argc, argv,  "-doc","");
    fn_root = getParameter(argc, argv,  "-root");
    virusRadius = textToFloat(getParameter(argc, argv, "-radius"));
    minVirusRadius = textToFloat(getParameter(argc, argv, "-min_radius"));
    dim = textToInteger(getParameter(argc, argv, "-dim"));
    fn_sym  = getParameter(argc, argv, "-sym","i3");
    verbose = checkParameter(argc, argv,"-verbose");
    removeCloseVertex = checkParameter(argc, argv,"-remove");
}

/* Show -------------------------------------------------------------------- */
void VirusVertex::show()
{
    std::cout << "input selfile:             " << fn_sel  << std::endl
    << "output files root:         " << fn_root << std::endl
    << "docfile :                  " << fn_doc  << std::endl
    << "virus radius:              " << virusRadius << std::endl
    << "minimun virus radius:      " << minVirusRadius << std::endl
    << "outputfile dimensions:     " << dim << std::endl
    << "symmetry:                  " << fn_sym << std::endl
    << "verbose:                   " << verbose << std::endl
    << "remove:                    " << removeCloseVertex<< std::endl
    ;
}

/* Usage ------------------------------------------------------------------- */
void VirusVertex::usage()
{
    std::cerr << "   -sel filename             : Selfile with image names\n"
    << "   -root filename            : Root name for output images\n"
    << "   -doc  filename  (optional): Auxiliary file with projection angles\n"
    << "   -radius float_number      : virus radius (distance from center\n"
    << "                               to vertex in pixels)\n"
    << "   -min_radius  float_number : extract vertex located at a radius greater\n"
    << "                               than min_radius\n"
    << "   -dim integer              : size of the extracted images (pixels)\n"
    << "   -sym symmetry flag (i3)   : symmetry description flag\n"
    << "   -verbose                  : set verbose mode on\n"
    << "   -remove                   : remove vertexs if closer than 'dim'\n"
    ;
}
void VirusVertex::loadIcosahedronVertex()
{
    vertices_vectors.push_back(vectorR3(0., 0., 1.));
    vertices_vectors.push_back(vectorR3(0.723606900230461, -0.525731185781806, 0.447213343087301));
    vertices_vectors.push_back(vectorR3(0.723606900230461, 0.525731185781806, 0.447213343087301));
    vertices_vectors.push_back(vectorR3(-0.276393239417711, 0.850650928976665, 0.447213343087301));
    vertices_vectors.push_back(vectorR3(-0.8944273172062, 0., 0.447213343087301));
    vertices_vectors.push_back(vectorR3(-0.276393239417711, -0.850650928976665, 0.447213343087301));
    vertices_vectors.push_back(vectorR3(0.8944273172062, 0., -0.447213343087301));
    vertices_vectors.push_back(vectorR3(0.276393242471372, 0.850650927984471, -0.447213343087301));
    vertices_vectors.push_back(vectorR3(-0.723606898343194, 0.525731188379405, -0.447213343087301));
    vertices_vectors.push_back(vectorR3(-0.723606898343194, -0.525731188379405, -0.447213343087301));
    vertices_vectors.push_back(vectorR3(0.276393242471372, -0.850650927984471, -0.447213343087301));
    vertices_vectors.push_back(vectorR3(0., 0., -1.));

    Matrix2D<double>  A(3, 3);
    if (symmetry  == pg_I || symmetry  == pg_I2)
    {
        Euler_angles2matrix(0,-31.7174745559,0, A);
    } else if (symmetry  == pg_I1)
    {//OK
        Euler_angles2matrix(0,-31.7174745559+90.,0, A);
    } else if (symmetry  == pg_I3)
    {//OK
        A.initIdentity();
    } else if (symmetry  == pg_I4)
    {//OK
        Euler_angles2matrix(0,-31.7174745559 *2.0,0, A);
    } else if (symmetry  == pg_I5)
    {//OK
        std::cerr << "ERROR: Symmetry pg_I5 not implemented" << std::endl;
        exit(0);
    } else
    {//OK
        std::cerr << "Unknown symmetry" << std::endl;
        exit(0);
    }
    for (int i = 0; i < 12; i++)
    {
        vertices_vectors[i]=A*vertices_vectors[i];
    }// for i
    //#define CHIMERA
    #ifdef CHIMERA
    std::ofstream filestr;
    filestr.open ("sym.bild");
    for (int i = 0; i < 12; i++)
    {
        filestr    << ".color red"
        << std::endl
        << ".sphere "
        << XX(vertices_vectors[i]) << " "
        << YY(vertices_vectors[i]) << " "
        << ZZ(vertices_vectors[i]) << " "
        << " .05"
        << std::endl
        ;
    }
    filestr.close();
    #endif
    #undef CHIMERA
}

void VirusVertex::ProcessAngles()
{
    double rot, tilt, psi, xoff, yoff, flip, weight;
    rot = tilt = psi = xoff = yoff = flip = weight = 0.;
    SF.go_beginning();
    Projection proj,proj_aux;
    int Ydim, Xdim;
    SF.ImgSize(Ydim, Xdim);
    SelFile SFout;
    SFout.clear();
    while (!SF.eof())
    {
        FileName fn_img = SF.NextImg();
        if (fn_img=="") break;
        proj.read(fn_img, false); //true means apply shifts 
        if (fn_doc == "")
        {
            rot  = proj.rot();
            tilt = proj.tilt();
            psi  = proj.psi();
            xoff = proj.Xoff();
            yoff = proj.Yoff();
            flip = proj.flip();
            weight = proj.weight();
        } else
        {
            get_angles_for_image(fn_img, rot, tilt, psi, xoff, yoff, flip, weight);
            proj.set_rot(rot);
            proj.set_tilt(tilt);
            proj.set_psi(psi);
            proj.set_Xoff(xoff);
            proj.set_Yoff(yoff);
            proj.set_flip(flip);
            proj.set_weight(weight);
        }
        Matrix2D<double> A;
        Matrix1D<double> projected_point(3); 
        Matrix1D<double> projected_point_2D(2); 
        std::vector <Matrix1D<double> > proj_vectors;
        for (int i = 0; i < 12; i++)
        {
            Uproject_to_plane(vertices_vectors[i],rot,tilt,psi,projected_point);
            XX(projected_point_2D)=XX(projected_point);
            YY(projected_point_2D)=YY(projected_point);
            proj_vectors.push_back(projected_point_2D);
        }
        bool scissor;
        for (int i = 0; i < 12; i++)
        {
            scissor=1;
            if (removeCloseVertex)
            {
                for (int j = 0; j < 12; j++)
                {
                    if(i==j) 
                        continue;
                    if((proj_vectors[i]-proj_vectors[j]).module()*virusRadius < dim)
                    {
                        scissor=0;
                        break;
                    }
    
                }
            }
            if (!scissor)
            {
                continue;
            }
            int radius =      proj_vectors[i].module()*virusRadius;
            if (radius > minVirusRadius)
            {            
                proj_aux=proj;
                FileName fn_tmp;
                proj_aux.set_Xoff(xoff + XX(proj_vectors[i])*virusRadius);
                proj_aux.set_Yoff(yoff + YY(proj_vectors[i])*virusRadius);
                A = proj_aux.get_transformation_matrix(true);
                if (!A.isIdentity())
                    proj_aux().selfApplyGeometryBSpline(A, 3, IS_INV, DONT_WRAP);
                fn_tmp = fn_img.without_extension() + "_";
                fn_tmp.compose(fn_tmp, i, "xmp");
                proj_aux.set_Xoff(0);//shift already aplied, same for flip? I do not think so
                proj_aux.set_Yoff(0);
                proj_aux().window((Ydim-dim)/2,(Xdim-dim)/2,(Ydim+dim)/2,(Xdim+dim)/2,0);
                proj_aux.write(fn_tmp);
                SFout.insert(fn_tmp, SelLine::ACTIVE);
            }
        }
    }
    FileName fn_tmp1;
    fn_tmp1= fn_sel.without_extension()+"_out.sel";
    SFout.write(fn_tmp1);
}

void VirusVertex::get_angles_for_image(const FileName &fn, double &rot,
    double &tilt, double &psi, double &xoff, double &yoff, double &flip,
    double &weight)
{
    if (DFangles.search_comment(fn))
    {
        rot    = DFangles(col_rot);
        tilt   = DFangles(col_tilt);
        psi    = DFangles(col_psi);
        xoff   = DFangles(col_xoff);
        yoff   = DFangles(col_yoff);
        if (col_flip < 0)
            flip   = 0.;
        else
            flip   = DFangles(col_flip);
        if (col_weight < 0)
            weight = 0.;
        else
            weight = DFangles(col_weight);
    }
    else
    {
        REPORT_ERROR(1, (std::string)"Prog_RecFourier_prm: Cannot find " + fn + " in docfile " + fn_doc);
    }
    
}

/* Main program ------------------------------------------------------------ */
void VirusVertex::run()
{

    double accuracy=1e-6;
    show();
    //read doc and sel files file
    if (fn_doc != "")
        DFangles.read(fn_doc);
        col_rot    = DFangles.getColNumberFromHeader("rot")  - 1;
        col_tilt   = DFangles.getColNumberFromHeader("tilt") - 1;
        col_psi    = DFangles.getColNumberFromHeader("psi")  - 1;
        col_xoff   = DFangles.getColNumberFromHeader("Xoff") - 1;
        col_yoff   = DFangles.getColNumberFromHeader("Yoff") - 1;
        col_flip   = DFangles.getColNumberFromHeader("Flip") - 1;
        col_weight = DFangles.getColNumberFromHeader("Weight") - 1;

    SF.read(fn_sel);
    //load icosahedron vertex
    symmetry=SL.read_sym_file(fn_sym, accuracy);
    loadIcosahedronVertex();
    //process one set of angles
    ProcessAngles();
}


