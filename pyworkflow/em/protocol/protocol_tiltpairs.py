# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es)
# *              Laura del Cano         (ldelcano@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'jmdelarosa@cnb.csic.es'
# *
# **************************************************************************
"""
This module contains protocols classes related to Random Conical Tilt.
"""

from protocol_import import ProtImport



class ProtImportImagesTiltPairs(ProtImport):
    """Common protocol to import a set of images in the project"""
        
    #--------------------------- DEFINE param functions --------------------------------------------
    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('pattern', PathParam, label=Message.LABEL_PATTERN,
                      help=Message.TEXT_PATTERN)
        form.addParam('checkStack', BooleanParam, label=Message.LABEL_CHECKSTACK, default=False)
        form.addParam('copyToProj', BooleanParam, label=Message.LABEL_COPYFILES, default=False)
        form.addParam('voltage', FloatParam, default=200,
                   label=Message.LABEL_VOLTAGE)
        form.addParam('sphericalAberration', FloatParam, default=2.26,
                   label=Message.LABEL_SPH_ABERRATION)
        form.addParam('ampContrast', FloatParam, default=0.1,
                      label=Message.LABEL_AMPLITUDE,
                      help=Message.TEXT_AMPLITUDE)
    
    #--------------------------- STEPS functions ---------------------------------------------------
    def importImages(self, pattern, checkStack, voltage, sphericalAberration, amplitudeContrast):
        """ Copy images matching the filename pattern
        Register other parameters.
        """
        from pyworkflow.em import findClass
        filePaths = glob(expandPattern(pattern))
        
        imgSet = self._createSet()
        acquisition = imgSet.getAcquisition()
        # Setting Acquisition properties
        acquisition.setVoltage(voltage)
        acquisition.setSphericalAberration(sphericalAberration)
        acquisition.setAmplitudeContrast(amplitudeContrast)
        
        # Call a function that should be implemented by each subclass
        self._setOtherPars(imgSet)
        
        outFiles = [imgSet.getFileName()]
        imgh = ImageHandler()
        img = imgSet.ITEM_TYPE()
        n = 1
        size = len(filePaths)
        
        filePaths.sort()
        
        for i, fn in enumerate(filePaths):
#             ext = os.path.splitext(basename(f))[1]
            dst = self._getExtraPath(basename(fn))
            if self.copyToProj:
                copyFile(fn, dst)
            else:
                createLink(fn, dst)
            
            if checkStack:
                _, _, _, n = imgh.getDimensions(dst)
            
            if n > 1:
                for index in range(1, n+1):
                    img.cleanObjId()
                    img.setFileName(dst)
                    img.setIndex(index)
                    imgSet.append(img)
            else:
                img.cleanObjId()
                img.setFileName(dst)
                imgSet.append(img)
            outFiles.append(dst)
            
            sys.stdout.write("\rImported %d/%d" % (i+1, size))
            sys.stdout.flush()
            
        print "\n"
        
        args = {}
        outputSet = self._getOutputSet(self._className)
        args[outputSet] = imgSet
        self._defineOutputs(**args)
        
        return outFiles
    
    #--------------------------- INFO functions ----------------------------------------------------
    def _validate(self):
        errors = []
        if not self.pattern.get():
            errors.append(Message.ERROR_PATTERN_EMPTY)
        else:
            filePaths = glob(expandPattern(self.pattern.get()))
        
            if len(filePaths) == 0:
                errors.append(Message.ERROR_PATTERN_FILES)

        return errors
    
    def _summary(self):
        summary = []
        outputSet = self._getOutputSet(self._className)
        if not hasattr(self, outputSet):
            summary.append("Output " + self._className + "s not ready yet.") 
            if self.copyToProj:
                summary.append("*Warning*: Import step could be take a long time due to the images are copying in the project.")
        else:
            summary.append("Import of %d " % getattr(self, outputSet).getSize() + self._className + "s from %s" % self.pattern.get())
            summary.append("Sampling rate : %0.2f A/px" % getattr(self, outputSet).getSamplingRate())
        
        return summary
    
    def _methods(self):
        methods = []
        outputSet = self._getOutputSet(self._className)
        if hasattr(self, outputSet):
            methods.append("%d " % getattr(self, outputSet).getSize() + self._className + "s has been imported")
            methods.append("with a sampling rate of %0.2f A/px" % getattr(self, outputSet).getSamplingRate())
            
        return methods
    
    #--------------------------- UTILS functions ---------------------------------------------------
    def getFiles(self):
        return getattr(self, self._getOutputSet(self._className)).getFiles()
    
    def _getOutputSet(self, setName):
        return "output" + setName + "s"


class ProtImportMicrographsTiltPairs(ProtImportImagesTiltPairs):
    """Protocol to import a set of micrographs to the project"""

    _className = 'Micrograph'
    _label = 'import micrographs'
    
    def _defineParams(self, form):
        ProtImportImages._defineParams(self, form)
        form.addParam('samplingRateMode', EnumParam, default=SAMPLING_FROM_IMAGE,
                   label=Message.LABEL_SAMP_MODE,
                   choices=[Message.LABEL_SAMP_MODE_1, Message.LABEL_SAMP_MODE_2])
        form.addParam('samplingRate', FloatParam, default=1, 
                   label=Message.LABEL_SAMP_RATE,
                   condition='samplingRateMode==%d' % SAMPLING_FROM_IMAGE)
        form.addParam('magnification', IntParam, default=50000,
                   label=Message.LABEL_MAGNI_RATE,
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
        form.addParam('scannedPixelSize', FloatParam, default=7.0,
                   label=Message.LABEL_SCANNED,
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
    
    def _insertAllSteps(self):
        self._createSet = self._createSetOfMicrographs
        self._insertFunctionStep('importImages', self.pattern.get(), self.checkStack.get(), 
                                 self.voltage.get(), self.sphericalAberration.get(), self.ampContrast.get()) #, self.samplingRate.get(),
    
    def _validate(self):
        errors = ProtImportImages._validate(self)
#         if self._checkMrcStack():
#             errors.append("The micrographs can't be a mrc stack")
        return errors
    
    def _setOtherPars(self, micSet):
        micSet.getAcquisition().setMagnification(self.magnification.get())
        
        if self.samplingRateMode == SAMPLING_FROM_IMAGE:
            micSet.setSamplingRate(self.samplingRate.get())
        else:
            micSet.setScannedPixelSize(self.scannedPixelSize.get())
    
    def _checkMrcStack(self):
        filePaths = glob(expandPattern(self.pattern.get()))
        imgh = ImageHandler()
        stack = False
        for f in filePaths:
            ext = os.path.splitext(basename(f))[1]
            _, _, _, n = imgh.getDimensions(f)
            if ext == ".mrc" and n > 1:
                stack = True
                break
        return stack
    
    

    
    