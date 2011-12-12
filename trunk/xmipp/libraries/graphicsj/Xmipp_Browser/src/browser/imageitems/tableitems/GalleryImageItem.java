/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package browser.imageitems.tableitems;

import xmipp.Filename;
import xmipp.MDLabel;
import xmipp.MetaData;
import browser.Cache;
import browser.DEBUG;
import browser.LABELS;
import ij.ImagePlus;
import xmipp.ImageGeneric;
import xmippij.XmippImageConverter;

/**
 *
 * @author Juanjo Vega
 */
public class GalleryImageItem extends AbstractGalleryImageItem {

    protected long id;
    protected MetaData md;
    protected int label;
    protected String originalValue;
    protected String path;
    protected long nimage;
    protected boolean readGeo;

    public GalleryImageItem(long id, MetaData md, int label, Cache cache) {
        super(cache);

        this.id = id;
        this.md = md;
        this.label = label;

        originalValue = md.getValueString(label, id);
        if (originalValue != null) {
            String field = md.getValueString(label, id, true);
            path = Filename.getFilename(field);
            nimage = Filename.getNimage(field);

            loadImageData();
        }
    }

    @Override
    protected ImagePlus loadPreview(int w, int h) {
        ImagePlus imp = null;

        if (readGeo) {
            try {
                ImageGeneric image = new ImageGeneric();
                image.readApplyGeo(getAbsoluteFileName(), md, id, w, h);

                imp = XmippImageConverter.convertImageGenericToImageJ(image);
                imp.setTitle(getOriginalValue());
            } catch (Exception ex) {
                DEBUG.printException(ex);
            }
        } else {
            imp = super.loadPreview(w, h);
        }

        return imp;
    }

    public boolean isEnabled() {
        return getValueInt(MDLabel.MDL_ENABLED) == 1;
    }

    public void setEnabled(boolean enabled) {
        md.setValueInt(MDLabel.MDL_ENABLED, enabled ? 1 : 0, id);
    }

    public void setReadGeo(boolean readGeo) {
        this.readGeo = readGeo;
    }

    public long getID() {
        return id;
    }

    public int getLabel() {
        return label;
    }

    public String getAbsoluteFileName() {
        return Filename.getFilename(path);
    }

    public long getNImage() {
        return nimage;
    }

    @Override
    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }

    @Override
    public int getNSlice() {
        return ImageGeneric.FIRST_SLICE;
    }

    @Override
    public String getTitle() {
        return originalValue;
    }

    public String getOriginalValue() {
        return originalValue;
    }

    public void setOriginalValue(String value) {
        originalValue = value;
    }

    public String getTooltipText() {
        return originalValue;//path + (isStack() ? " [" + getNImage() + "]" : "");
    }

    public Object getLabelValue(int label) {
        Class class_ = MetaData.getLabelType(label);

        // Special label.
        if (label == MDLabel.MDL_ENABLED) {
            return md.getValueInt(label, id) > 0 ? Boolean.TRUE : Boolean.FALSE;
        }

        // Rest of them...
        if (class_ == Integer.class) {
            return md.getValueInt(label, id);
        }
        if (class_ == Double.class) {
            return md.getValueDouble(label, id);
        }
        if (class_ == String.class) {
            return md.getValueString(label, id);
        }

        return LABELS.LABEL_UNKNOWN;
    }

    // Metadata related methods.
    protected String getValueString(int label) {
        return md.getValueString(label, id, true);
    }

    protected boolean getValueBoolean(int label) {
        return md.getValueBoolean(label, id);
    }

    protected double getValueDouble(int label) {
        return md.getValueDouble(label, id);
    }

    protected double getValueInt(int label) {
        return md.getValueInt(label, id);
    }

    @Override
    public String toString() {
        return originalValue;
    }
}
