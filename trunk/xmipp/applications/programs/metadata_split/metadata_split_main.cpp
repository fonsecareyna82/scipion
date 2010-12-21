/***************************************************************************
 *
 * Authors:     Sjors Scheres (scheres@cnb.csic.es)
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
 *  e-mail address 'xmipp@cnb.csic.es'
 ***************************************************************************/

#include <data/metadata.h>
#include <data/args.h>
#include <data/program.h>

class ProgMetadataSplit: public XmippProgram
{
    FileName fn_in, fn_out, fn_root;
    std::string sortLabelStr;
    MDLabel sortLabel;
    MetaData  SFin;
    MetaData *SFtmp, *SFtmp2;
    std::vector<MetaData> mdVector;
    bool     dont_randomize;
    bool     dont_sort;
    int N;

protected:

    void defineParams()
    {
        addUsageLine("Split a selfile (randomly by default) in any number of equally sized output selfiles.");
        addUsageLine("Only active entries in the input file will be written to the output files.");
        addUsageLine("Example: Splits input.sel in two parts (output_1.sel and output_2.sel) ");
        addUsageLine("  xmipp_metadata_split -i input.sel -o output");
        addUsageLine("Example: Splits input.sel in 4 output files without generating random groups.");
        addUsageLine("  xmipp_metadata_split -i input.sel -n 4 --dont_randomize  ");
        addParamsLine("    -i <inputSelfile>    : Input MetaData File");
        addParamsLine("  [ -n <n_metadatas=2> ] : Number of output MetaDatas");
        addParamsLine("  [ -o <rootname=\"\"> ] : Rootname for output MetaDatas");
        addParamsLine("                         : output will be rootname_<n>.xpd");
        addParamsLine("  [--dont_randomize ]    : Do not generate random groups");
        addParamsLine("  [--dont_sort ]         : Do not sort the output MetaData");
        addParamsLine("  [-l <label=\"image\">] : sort using a label, default image");
    }

    void readParams()
    {

        fn_in = getParam("-i");
        N = getIntParam("-n");
        fn_root = getParam("-o");
        dont_randomize = checkParam("--dont_randomize");
        dont_sort      = checkParam("--dont_sort");

        sortLabelStr = "objId"; //if not sort, by default is objId
        if(!dont_sort)
            sortLabelStr = getParam("-l");

        sortLabel = MDL::str2Label(sortLabelStr);
        if (sortLabel == MDL_UNDEFINED)
            REPORT_ERROR(ERR_MD_UNDEFINED, (std::string)"Unrecognized label '" + sortLabelStr + "'");

        if (fn_root == "")
            fn_root = fn_in.withoutExtension();
    }

public:
    void run()
    {

        SFin.read(fn_in);

        if (!dont_randomize)
        {
            SFtmp = new MetaData();
            SFtmp->randomize(SFin);
        }
        else
            SFtmp = &SFin;

        int Num_images = (int)SFtmp->size();
        int Num_groups = XMIPP_MIN(N, Num_images);
        SFtmp->split(Num_groups, mdVector); //Split MD in Num_groups
        //Write splitted groups to disk
        for (int i = 0; i < Num_groups; i++)
        {
            fn_out = fn_root;
            if (Num_groups != 1 )
            {
                //std::string num = "_" + integerToString(i + 1);
                fn_out += "_" + integerToString(i + 1);
            }
            //fn_out += ".xmd";
            fn_out += ".sel";
            if(!dont_sort)
                SFtmp->sort(mdVector[i], sortLabel);
            else
                SFtmp = &(mdVector[i]);
            SFtmp->write(fn_out);
        }
    }

}
;//end of class ProgMetadataSplit

/* MAIN -------------------------------------------------------------------- */
int main(int argc, char *argv[])
{
    try
    {
        ProgMetadataSplit program;
        program.read(argc, argv);
        program.run();
    }
    catch (XmippError xe)
    {
        std::cerr << xe;
        return 1;
    }
    return 0;
}

